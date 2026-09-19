"""
Created December 29, 2025

@author montreal91
"""
import csv
import time
from dataclasses import dataclass
from typing import Dict

from core.club import Club
from core.club_data import load_club_info_by_id
from core.financial import DdTransaction
from core.game import Game
from core.player import Player


@dataclass(frozen=True)
class CreateNewGameCommand:
    game_id: str


@dataclass(frozen=True)
class CreateNewGameCommandResult:
    game_id: str


class CreateNewGameCommandHandler:
    def __init__(
            self,
            game_repository,
            game_parameters,
            club_provider,
    ):
        self._game_repository = game_repository
        self._parameters = game_parameters
        self._club_provider = club_provider

    def __call__(self, command: CreateNewGameCommand) -> CreateNewGameCommandResult:
        game = Game(
            game_id=command.game_id,
            params=self._parameters,
            created_ts=time.time_ns() // 1_000_000,
            updated_ts=time.time_ns() // 1_000_000,
        )
        self._game_repository.save_game(game)

        clubs = init_clubs_for_game(game_id=command.game_id)
        self._club_provider.save_clubs(clubs.values())

        game.tmp_init()

        return CreateNewGameCommandResult(game.game_id)


def _add_club(clubs: Dict[str, Club], game_id: str, club_data: Dict[str, str]):
    club = Club(
        club_id=club_data["club_id"],
        game_id=game_id,
        name=club_data["name"],
        coach_power=int(club_data["coach_power"]),
        league_id=club_data["league_id"] or None,
    )

    for index in range(1, 6):
        club.add_fame(int(club_data[f"fame_{index}"]))

    club.account.ProcessTransaction(DdTransaction(
        int(club_data["balance"]),
        "Initial balance",
    ))

    clubs[club.club_id] = club


def init_clubs_for_game(game_id: str) -> Dict[str, Club]:
    clubs: Dict[str, Club] = {}

    with open("data/clubs.csv", newline="", encoding="utf-8-sig") as clubs_file:
        for club_data in csv.DictReader(clubs_file):
            _add_club(clubs=clubs, game_id=game_id, club_data=club_data)

    load_club_info_by_id(list(clubs.keys()))

    with open(
            "data/players.csv", newline="", encoding="utf-8-sig"
    ) as players_file:
        for player_data in csv.DictReader(players_file):
            club = clubs.get(player_data["club_id"])
            if club is None:
                raise ValueError(
                    f"Unknown club {player_data['club_id']} for player "
                    f"{player_data['player_id']}."
                )

            player = Player(
                first_name=player_data["first_name"],
                second_name=player_data["second_name"],
                last_name=player_data["last_name"],
                technique=int(player_data["technique"]),
                endurance=int(player_data["endurance"]),
                age=int(player_data["age"]),
            )
            player._player_id = player_data["player_id"]
            player._exhaustion = int(player_data["exhaustion"])
            player._experience = int(player_data["experience"])
            player._skill_points = int(player_data["skill_points"])
            player._current_stamina = int(player_data["current_stamina"])
            player._reputation = int(player_data["reputation"])
            club.add_player(player)
            if player_data["has_next_contract"].lower() == "true":
                club.contract_player(player.player_id)

    return clubs

