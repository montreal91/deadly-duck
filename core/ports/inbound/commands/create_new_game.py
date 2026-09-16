"""
Created December 29, 2025

@author montreal91
"""
import json
import time
from dataclasses import dataclass
from typing import Any
from typing import Dict

from core.club import Club
from core.club import ClubPlayerSlot
from core.financial import DdTransaction
from core.game import Game
from core.player import Player
from core.serialization import DdJsonDecoder


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


def _add_club(
        clubs: Dict[str, Club],
        game_id: str,
        club_data: Dict[str, Any],
):
    club = Club(
        club_id=club_data["club_id"],
        game_id=game_id,
        name=club_data["name"],
        coach_power=club_data["coach_power"],
    )

    for value in club_data["fame"]:
        club.add_fame(value)

    for slot in club_data["player_data"]:
        club.add_player(slot.player)
        if slot.has_next_contract:
            club.contract_player(player_id=slot.player.player_id)

    club.account.ProcessTransaction(DdTransaction(
        club_data["balance"],
        "Initial balance",
    ))

    clubs[club.club_id] = club


def init_clubs_for_game(game_id: str) -> Dict[str, Club]:
    clubs = {}
    decoder = DdJsonDecoder()
    decoder.register(Player)
    decoder.register(ClubPlayerSlot)

    with open("data/clubs.json", "r", encoding="utf-8") as data_file:
        club_data = json.load(data_file, object_hook=decoder)

    for club in club_data:
        _add_club(clubs=clubs, game_id=game_id, club_data=club)

    return clubs

