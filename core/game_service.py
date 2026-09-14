"""
Game manipulation stuff.

Created May 11, 2024

@author montreal91
"""
from typing import List
from typing import NamedTuple
from typing import Optional


class MainScreenInfo(NamedTuple):
    day: str
    balance: int
    club_name: str


class PlayerListInfo(NamedTuple):
    player_id: str
    name: str
    level: int
    actual_technique: float
    technique: float
    endurance: float
    current_stamina: int
    maximum_stamina: int
    coach_level: int
    is_selected: bool
    age: int
    exhaustion: int


class OpponentPlayerInfo(NamedTuple):
    player_id: str
    name: str
    level: int
    technique: float
    endurance: float
    maximum_stamina: int
    age: int
    exhaustion: int


class PlayerListScreenInfo(NamedTuple):
    players: List[PlayerListInfo]
    practice_cost: int


class AgentListInfo(NamedTuple):
    player_id: int
    age: int
    technique: float
    endurance: float
    contract_cost: int
    name: str


class CourtInfo(NamedTuple):
    capacity: int
    rent_cost: int
    ticket_price: int


class SavedGamesInfo(NamedTuple):
    names: List[str]


class OpponentInfo(NamedTuple):
    club_name: str
    player: Optional[PlayerListInfo]


class PlayerSelectionScreenInfo(NamedTuple):
    players: List[PlayerListInfo]
    opponent: OpponentInfo


class GameService:
    def __init__(
            self,
            game_repository,
            game_parameters,
            competition_repository=None,
    ):
        self._game_repository = game_repository
        self._parameters = game_parameters
        self._competition_repository = competition_repository

    def get_saved_games(self):
        return SavedGamesInfo(names=self._game_repository.get_game_ids())

    def get_main_screen_info(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        context = game.get_context(manager_club_id)

        info = MainScreenInfo(
            day=context["day"],
            balance=context["balance"],
            club_name=context["club_name"],
        )

        return info

    def get_player_selection_gui_info(self, game_id, manager_club_id):
        context = self._game_repository.get_game(game_id).get_context(manager_club_id)

        players = [
            _player_to_row_info(
                player.player, player.is_selected, player.coach_level
            )
            for player in context["user_players"]
        ]

        return PlayerSelectionScreenInfo(
            players=players,
            opponent=_opponent_dto_to_info(context.get("opponent", None)),
        )

    def get_manager_club_id(self, game_id):
        game = self._game_repository.get_game(game_id)
        if game is None:
            return -1
        return game.manager_club_id

    def _save_competitions(
            self,
            game,
            previous_competition,
            previous_season_index: int,
    ):
        if self._competition_repository is None:
            return

        if previous_competition is not game.competition:
            self._competition_repository.save(
                game_id=game.game_id,
                competition=previous_competition,
                season_index=previous_season_index,
                is_current=False,
            )

        self._competition_repository.save(
            game_id=game.game_id,
            competition=game.competition,
            season_index=game.season_index,
        )


def _player_to_row_info(player, is_selected, coach_level):
    # Again, this method is weird, but okay for now :)
    plr = {
        "player_id": player.player_id,
        "name": f"{player.first_name} {player.last_name}",
        "level": player.level,
        "actual_technique": player.actual_technique,
        "technique": player.technique,
        "endurance": player.endurance,
        "current_stamina": player.current_stamina,
        "maximum_stamina": player.max_stamina, "coach_level": coach_level,
        "is_selected": is_selected,
        "age": player.age,
        "exhaustion": player.exhaustion,
    }

    return PlayerListInfo(**plr)


def _opponent_dto_to_info(opponent_dto):
    if opponent_dto is None:
        return None

    player_info = None

    if opponent_dto.player is not None:
        player_info = OpponentPlayerInfo(
            player_id=opponent_dto.player.player_id,
            name=f"{opponent_dto.player.first_name} {opponent_dto.player.last_name}",
            level=opponent_dto.player.level,
            technique=opponent_dto.player.technique,
            endurance=opponent_dto.player.endurance,
            maximum_stamina=opponent_dto.player.max_stamina,
            age=opponent_dto.player.age,
            exhaustion=opponent_dto.player.exhaustion,
        )

    return OpponentInfo(
        club_name=opponent_dto.club_name,
        player=player_info,
    )
