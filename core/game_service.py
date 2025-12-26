"""
Game manipulation stuff.

Created May 11, 2024

@author montreal91
"""
from typing import List, Optional
from typing import NamedTuple

from core.club_repository import ClubRepository
from core.game import Game
from core.game import GameParams
from core.game_repository import GameRepository


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


class OpponentPlayerInfo(NamedTuple):
    player_id: int
    name: str
    level: int
    technique: float
    endurance: float
    maximum_stamina: int
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


class UpdateResult(NamedTuple):
    success: bool
    reason: str


class FameInfo(NamedTuple):
    club_id: int
    club_name: str
    fame: int


class FameRatingsQuery(NamedTuple):
    game_id: str


class FameRatingsQueryResult(NamedTuple):
    fame_ratings: List[FameInfo]


class SavedGamesInfo(NamedTuple):
    names: List[str]


class OpponentInfo(NamedTuple):
    club_name: str
    match_surface: str
    player: Optional[PlayerListInfo]


class PlayerSelectionScreenInfo(NamedTuple):
    players: List[PlayerListInfo]
    opponent: OpponentInfo


class FameQueryHandler:
    _club_repository: ClubRepository

    def __init__(self, club_repository: ClubRepository):
        self._club_repository = club_repository

    def handle(self, request: FameRatingsQuery) -> FameRatingsQueryResult:
        clubs = self._club_repository.get_all_clubs(request.game_id)
        fames = [
            FameInfo(club_id=club.club_id, club_name=club.name, fame=club.fame)
            for club in clubs
        ]

        return FameRatingsQueryResult(
            fame_ratings=sorted(fames, key=lambda fame: fame.fame, reverse=True),
        )


class GameService:
    _game_repository: GameRepository
    _game_parameters: GameParams

    def __init__(
            self,
            game_repository: GameRepository,
            game_parameters: GameParams,
            fame_query_handler: FameQueryHandler
    ):
        self._game_repository = game_repository
        self._parameters = game_parameters
        self._fame_query_handler = fame_query_handler

    def create_new_game(self, game_id, manager_club_id):
        self._game_repository.save_game(Game(
            params=self._parameters,
            game_id=game_id,
            manager_club_id=manager_club_id
        ))

    def get_saved_games(self):
        return SavedGamesInfo(names=self._game_repository.get_game_ids())

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
            _agent_to_list_info(player[0], i, player[1])
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

    def get_player_selection_gui_info(self, game_id, manager_club_id):
        context = self._game_repository.get_game(game_id).get_context(manager_club_id)

        players = [
            _player_to_row_info(
                player.player, i, player.is_selected, player.coach_level
            )
            for i, player in enumerate(context["user_players"])
        ]

        return PlayerSelectionScreenInfo(
            players=players,
            opponent=_opponent_dto_to_info(context.get("opponent", None)),
        )


    def get_player_list_info(self, game_id, manager_club_id):
        context = self._game_repository.get_game(game_id).get_context(
            manager_club_id
        )

        players = [
            _player_to_row_info(
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

    def get_court_info(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        court = game.get_context(manager_club_id)["court"]

        return CourtInfo(**court)

    def fire_player(self, game_id, manager_club_id, player_id):
        game = self._game_repository.get_game(game_id)
        game.fire_player(player_id, manager_club_id)
        self._game_repository.save_game(game)

    def hire_player(self, game_id, manager_club_id, surface):
        game = self._game_repository.get_game(game_id)
        game.hire_new_player(surface, manager_club_id)
        self._game_repository.save_game(game)

    def sign_player(self, game_id, manager_club_id, player_id):
        game = self._game_repository.get_game(game_id)
        game.sign_player(club_id=manager_club_id, player_id=player_id)
        self._game_repository.save_game(game)

    def save_game(self, game_id):
        game = self._game_repository.get_game(game_id)

        if game is None:
            return

        self._game_repository.save_game(game, persistent_save=True)

    def get_game_context(self, game_id):
        game = self._game_repository.get_game(game_id)
        return game.get_context(game.manager_club_id)

    def next_day(self, game_id):
        game = self._game_repository.get_game(game_id)
        if game is None:
            return UpdateResult(success=False, reason=f"Game with id={game_id} not found")
        res, reason = game.update()
        self._game_repository.save_game(game, persistent_save=True)
        return UpdateResult(success=res, reason=reason)

    def proceed(self, game_id):
        game = self._game_repository.get_game(game_id)
        if game is None:
            return
        game.proceed_to_next_competition()
        self._game_repository.save_game(game, persistent_save=True)

    def set_player(self, game_id, manager_club_id, player_id):
        game = self._game_repository.get_game(game_id)
        if game is None:
            return
        game.select_player(player_id=player_id, club_id=manager_club_id)
        self._game_repository.save_game(game)

    def get_fames(self, game_id) -> FameRatingsQueryResult:
        return self._fame_query_handler.handle(FameRatingsQuery(game_id=game_id))

    def get_manager_club_id(self, game_id):
        game = self._game_repository.get_game(game_id)
        if game is None:
            return -1
        return game.manager_club_id


def _agent_to_list_info(player, player_id, contract_cost):
    return AgentListInfo(
        player_id=player_id,
        age=player.age,
        technique=player.technique / 10,
        endurance=player.endurance,
        speciality=player.speciality,
        contract_cost=contract_cost,
        name=f"{player.first_name} {player.last_name}",
    )

def _player_to_row_info(player, player_id, is_selected, coach_level):
    # Again, this method is weird, but okay for now :)
    plr = {
        "player_id": player_id,
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
        "speciality": player.speciality
    }

    return PlayerListInfo(**plr)


def _opponent_dto_to_info(opponent_dto):
    if opponent_dto is None:
        return None

    player_info = None

    if opponent_dto.player is not None:
        player_info = OpponentPlayerInfo(
            player_id=-1,
            name=f"{opponent_dto.player.first_name} {opponent_dto.player.last_name}",
            level=opponent_dto.player.level,
            technique=opponent_dto.player.technique,
            endurance=opponent_dto.player.endurance,
            maximum_stamina=opponent_dto.player.max_stamina,
            age=opponent_dto.player.age,
            exhaustion=opponent_dto.player.exhaustion,
            speciality=opponent_dto.player.speciality,
        )

    return OpponentInfo(
        club_name=opponent_dto.club_name,
        match_surface=opponent_dto.match_surface,
        player=player_info,
    )
