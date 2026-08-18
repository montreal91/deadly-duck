"""
Created August 17, 2026

@author montreal91
"""
from typing import List
from typing import NamedTuple


class PracticeScreenQuery(NamedTuple):
    game_id: str
    manager_club_id: int


class PlayerPracticeInfo(NamedTuple):
    player_id: str
    pos: int
    name: str
    age: int
    level: int
    technique: float
    endurance: float
    coach_level: int
    experience: int
    next_level_experience: int
    practice_cost: int


class PracticeScreenQueryResult(NamedTuple):
    success: bool
    balance: int
    players: List[PlayerPracticeInfo]


class PracticeScreenQueryHandler:
    def __init__(self, game_repository):
        self._game_repository = game_repository

    def __call__(self, query: PracticeScreenQuery) -> PracticeScreenQueryResult:
        game = self._game_repository.get_game(query.game_id)

        if game is None:
            return PracticeScreenQueryResult(
                success=False,
                balance=0,
                players=[],
            )

        context = game.get_context(query.manager_club_id)
        players = [
            _player_slot_to_practice_info(game, player_slot, player_pos)
            for player_pos, player_slot in enumerate(context["user_players"])
        ]

        return PracticeScreenQueryResult(
            success=True,
            balance=context["balance"],
            players=players,
        )


def _player_slot_to_practice_info(game, player_slot, player_pos):
    player = player_slot.player
    return PlayerPracticeInfo(
        player_id=player.player_id,
        pos=player_pos,
        name=f"{player.first_name} {player.last_name}",
        age=player.age,
        level=player.level,
        technique=player.technique,
        endurance=player.endurance,
        coach_level=player_slot.coach_level,
        experience=player.experience,
        next_level_experience=player.next_level_exp,
        practice_cost=game._practice_calculator(
            player.level,
            player_slot.coach_level,
        ),
    )
