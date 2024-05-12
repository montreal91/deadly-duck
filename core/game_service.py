"""
Game manipulation stuff.

Created May 11, 2024

@author montreal91
"""

from typing import List
from typing import NamedTuple

from core.game_repostory import GameRepository
from core.game import Game


class MainScreenInfo(NamedTuple):
    day: int
    balance: int
    club_name: str


class PlayerListInfo(NamedTuple):
    player_id: int
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
    speciality: str


class PlayerListScreenInfo(NamedTuple):
    players: List[PlayerListInfo]
    practice_cost: int


class AgentListInfo(NamedTuple):
    player_id: int
    age: int
    technique: float
    endurance: float
    speciality: str
    contract_cost: int
    name: str


class CourtInfo(NamedTuple):
    capacity: int
    rent_cost: int
    ticket_price: int


class GameService:
    def __init__(self, game_repository: GameRepository, game_parameters):
        self._game_repository = game_repository
        self._parameters = game_parameters

    def create_new_game(self, game_id, manager_club_id):
        self._game_repository.save_game(Game(
            params=self._parameters,
            game_id=game_id,
            manager_club_id=manager_club_id
        ))

    def get_manager_club(self, game_id):
        game = self._game_repository.get_game(game_id)

        if game is None:
            return None

        return game.manager_club_id

    def game_is_over(self, game_id):
        game = self._game_repository.get_game(game_id)
        return game.is_over

    def get_agents_list_screen_info(self, game_id, manager_club_id):
        # This should actually sit in PlayerService
        # Or, better, use ports and adapters and make it a query
        game = self._game_repository.get_game(game_id)

        if game is None:
            return None

        game_agents = game.get_context(manager_club_id)["free_agents"]
        return [
            self._agent_to_list_info(player[0], i, player[1])
            for i, player in enumerate(game_agents)
        ]

    def get_main_screen_info(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        context = game.get_context(manager_club_id)

        info = MainScreenInfo(
            day=context["day"],
            balance=context["balance"],
            club_name=context["club_name"],
        )

        return info

    def get_player_list_info(self, game_id, manager_club_id):
        context = self._game_repository.get_game(game_id).get_context(
            manager_club_id
        )

        players = [
            self._player_to_row_info(
                player.player, i, player.is_selected, player.coach_level
            )
            for i, player in enumerate(context["user_players"])
        ]

        return PlayerListScreenInfo(
            players=players,
            practice_cost=context["practice_cost"],
        )

    def hire_free_agent(self, game_id, manager_club_id, agent_id):
        game = self._game_repository.get_game(game_id)
        game.hire_free_agent(manager_club_id, agent_id)
        self._game_repository.save_game(game)

    def select_coach_for_player(self, game_id, manager_club_id, coach_quality, player_id):
        game = self._game_repository.get_game(game_id)
        game.select_coach_for_player(
            coach_index=coach_quality,
            player_index=player_id,
            club_index=manager_club_id,
        )
        self._game_repository.save_game(game)

    def select_court_for_club(self, game_id, manager_club_id, court_type):
        game = self._game_repository.get_game(game_id)
        game.select_court(manager_club_id, court_type)
        self._game_repository.save_game(game)

    def get_court_info(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        court = game.get_context(manager_club_id)["court"]

        return CourtInfo(**court)

    def _player_to_row_info(self, player, player_id, is_selected, coach_level):
        # Again, this method is weird, but okay for now :)
        plr = {}
        plr["player_id"] = player_id
        plr["name"] = f"{player.first_name} {player.last_name}"
        plr["level"] = player.level
        plr["actual_technique"] = player.actual_technique
        plr["technique"] = player.technique
        plr["endurance"] = player.endurance
        plr["current_stamina"] = player.current_stamina
        plr["maximum_stamina"] = player.max_stamina
        plr["coach_level"] = coach_level
        plr["is_selected"] = is_selected
        plr["age"] = player.age
        plr["exhaustion"] = player.exhaustion
        plr["speciality"] = player.speciality

        return PlayerListInfo(**plr)

    def _agent_to_list_info(self, player, player_id, contract_cost):
        return AgentListInfo(
            player_id=player_id,
            age=player.age,
            technique=player.technique / 10,
            endurance=player.endurance,
            speciality=player.speciality,
            contract_cost=contract_cost,
            name=f"{player.first_name} {player.last_name}",
        )
