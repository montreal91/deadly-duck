"""
Created September 15, 2026

@author montreal91
"""
from json import dumps
from json import loads
from sqlite3 import Row
from typing import Dict
from typing import List

from core.match_result import MatchResult
from core.regular_championship import RegularChampionshipStandingsRow
from core.set_result import DdSetStatuses
from core.set_result import SetResult


class MatchResultRepository:
    _TMP_INSTANCE = None

    @staticmethod
    def tmp_init(conn=None):
        MatchResultRepository._TMP_INSTANCE = MatchResultRepository(conn)

    @staticmethod
    def tmp_get_instance() -> "MatchResultRepository":
        return MatchResultRepository._TMP_INSTANCE

    def __init__(self, conn=None):
        self._conn = conn
        if self._conn is not None:
            self._conn.row_factory = Row

    def save_match_results(self, game_id: str, match_results: List[MatchResult]):
        if self._conn is None:
            raise RuntimeError("MatchResultRepository has no SQLite connection.")

        with self._conn:
            for result in match_results:
                competition_id = self._get_competition_id(
                    game_id=game_id,
                    match_id=result.match_id,
                )
                self._conn.execute(
                    """
                    INSERT INTO match_result (
                        game_id,
                        competition_id,
                        match_id,
                        home_club_id,
                        away_club_id,
                        home_player_id,
                        away_player_id,
                        home_player_snapshot,
                        away_player_snapshot,
                        home_sets,
                        away_sets,
                        home_games,
                        away_games,
                        full_score,
                        attendance,
                        income
                    )
                    VALUES (
                        :game_id,
                        :competition_id,
                        :match_id,
                        :home_club_id,
                        :away_club_id,
                        :home_player_id,
                        :away_player_id,
                        :home_player_snapshot,
                        :away_player_snapshot,
                        :home_sets,
                        :away_sets,
                        :home_games,
                        :away_games,
                        :full_score,
                        :attendance,
                        :income
                    )
                    ON CONFLICT(game_id, match_id) DO UPDATE SET
                        competition_id = excluded.competition_id,
                        home_club_id = excluded.home_club_id,
                        away_club_id = excluded.away_club_id,
                        home_player_id = excluded.home_player_id,
                        away_player_id = excluded.away_player_id,
                        home_player_snapshot = excluded.home_player_snapshot,
                        away_player_snapshot = excluded.away_player_snapshot,
                        home_sets = excluded.home_sets,
                        away_sets = excluded.away_sets,
                        home_games = excluded.home_games,
                        away_games = excluded.away_games,
                        full_score = excluded.full_score,
                        attendance = excluded.attendance,
                        income = excluded.income
                    """,
                    {
                        "game_id": game_id,
                        "competition_id": competition_id,
                        "match_id": result.match_id,
                        "home_club_id": result.home_pk,
                        "away_club_id": result.away_pk,
                        "home_player_id": _player_id(result.home_player_snapshot),
                        "away_player_id": _player_id(result.away_player_snapshot),
                        "home_player_snapshot": _dump_snapshot(
                            result.home_player_snapshot,
                        ),
                        "away_player_snapshot": _dump_snapshot(
                            result.away_player_snapshot,
                        ),
                        "home_sets": result.home_sets,
                        "away_sets": result.away_sets,
                        "home_games": result.home_games,
                        "away_games": result.away_games,
                        "full_score": result.full_score,
                        "attendance": result.attendance,
                        "income": result.income,
                    },
                )

    def get_latest_results(self, game_id: str, competition_id: str) -> List[MatchResult]:
        if self._conn is None:
            raise RuntimeError("MatchResultRepository has no SQLite connection.")

        rows = self._conn.execute(
            """
            SELECT
                result.match_id,
                result.home_club_id,
                result.away_club_id,
                result.home_player_snapshot,
                result.away_player_snapshot,
                result.full_score,
                result.attendance,
                result.income
            FROM match_result AS result
            JOIN scheduled_match AS match
              ON match.game_id = result.game_id
             AND match.match_id = result.match_id
            WHERE result.game_id = :game_id
              AND result.competition_id = :competition_id
              AND match.schedule_day = (
                  SELECT MAX(latest_match.schedule_day)
                  FROM match_result AS latest_result
                  JOIN scheduled_match AS latest_match
                    ON latest_match.game_id = latest_result.game_id
                   AND latest_match.match_id = latest_result.match_id
                  WHERE latest_result.game_id = :game_id
                    AND latest_result.competition_id = :competition_id
              )
            ORDER BY result.match_id
            """,
            {
                "game_id": game_id,
                "competition_id": competition_id,
            },
        ).fetchall()

        return [
            _match_result_from_row(row)
            for row in rows
        ]

    def get_regular_championship_standings(
            self,
            game_id: str,
            competition_id: str
    ) -> List[RegularChampionshipStandingsRow]:
        if self._conn is None:
            raise RuntimeError("MatchResultRepository has no SQLite connection.")

        standings = self._make_empty_regular_championship_standings(
            game_id=game_id,
            competition_id=competition_id,
        )

        rows = self._conn.execute(
            """
            SELECT
                home_club_id,
                away_club_id,
                home_sets,
                away_sets,
                home_games,
                away_games
            FROM match_result
            WHERE game_id = :game_id
              AND competition_id = :competition_id
            ORDER BY match_id
            """,
            {
                "game_id": game_id,
                "competition_id": competition_id,
            },
        ).fetchall()

        for row in rows:
            _ensure_standings_row(standings, row["home_club_id"])
            _ensure_standings_row(standings, row["away_club_id"])

            home_standing = standings[row["home_club_id"]]
            away_standing = standings[row["away_club_id"]]

            standings[row["home_club_id"]] = RegularChampionshipStandingsRow(
                club_id=home_standing.club_id,
                matches_played=home_standing.matches_played + 1,
                sets_won=home_standing.sets_won + row["home_sets"],
                games_won=home_standing.games_won + row["home_games"],
            )
            standings[row["away_club_id"]] = RegularChampionshipStandingsRow(
                club_id=away_standing.club_id,
                matches_played=away_standing.matches_played + 1,
                sets_won=away_standing.sets_won + row["away_sets"],
                games_won=away_standing.games_won + row["away_games"],
            )

        return sorted(
            standings.values(),
            key=lambda x: (x.sets_won, x.games_won),
            reverse=True,
        )

    def _make_empty_regular_championship_standings(
            self,
            game_id: str,
            competition_id: str,
    ) -> Dict[str, RegularChampionshipStandingsRow]:
        rows = self._conn.execute(
            """
            SELECT home_club_id, away_club_id
            FROM scheduled_match
            WHERE game_id = :game_id
              AND competition_id = :competition_id
            ORDER BY schedule_day, match_id
            """,
            {
                "game_id": game_id,
                "competition_id": competition_id,
            },
        ).fetchall()

        standings = {}
        for row in rows:
            _ensure_standings_row(standings, row["home_club_id"])
            _ensure_standings_row(standings, row["away_club_id"])

        return standings

    def _get_competition_id(self, game_id: str, match_id: str) -> str:
        row = self._conn.execute(
            """
            SELECT competition_id
            FROM scheduled_match
            WHERE game_id = :game_id
              AND match_id = :match_id
            """,
            {
                "game_id": game_id,
                "match_id": match_id,
            },
        ).fetchone()

        if row is None:
            raise RuntimeError(f"Scheduled match {match_id} was not found.")

        return row["competition_id"]


def _player_id(player_snapshot):
    if player_snapshot is None:
        return None
    return player_snapshot.get("player_id")


def _dump_snapshot(player_snapshot):
    if player_snapshot is None:
        return None
    return dumps(player_snapshot)


def _ensure_standings_row(
        standings: Dict[str, RegularChampionshipStandingsRow],
        club_id: str,
):
    if club_id in standings:
        return

    standings[club_id] = RegularChampionshipStandingsRow(
        club_id=club_id,
        matches_played=0,
        sets_won=0,
        games_won=0,
    )


def _match_result_from_row(row) -> MatchResult:
    result = MatchResult()
    result.match_id = row["match_id"]
    result.home_pk = row["home_club_id"]
    result.away_pk = row["away_club_id"]
    result.home_player_snapshot = _load_snapshot(row["home_player_snapshot"])
    result.away_player_snapshot = _load_snapshot(row["away_player_snapshot"])
    result.attendance = row["attendance"]
    result.income = row["income"]

    for set_result in _parse_full_score(row["full_score"]):
        result.AddSetResult(set_result)

    return result


def _load_snapshot(player_snapshot):
    if player_snapshot is None:
        return None
    return loads(player_snapshot)


def _parse_full_score(full_score: str) -> List[SetResult]:
    if not full_score:
        return []

    return [
        _parse_set_score(set_score)
        for set_score in full_score.split()
    ]


def _parse_set_score(set_score: str) -> SetResult:
    home, away = set_score.split(":")

    if home == "Ret":
        return SetResult(
            home_games=0,
            away_games=int(away),
            set_status=DdSetStatuses.HOME_RETIRED,
        )
    if away == "Ret":
        return SetResult(
            home_games=int(home),
            away_games=0,
            set_status=DdSetStatuses.AWAY_RETIRED,
        )

    return SetResult(
        home_games=int(home),
        away_games=int(away),
        set_status=DdSetStatuses.REGULAR,
    )
