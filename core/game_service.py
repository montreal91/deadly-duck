"""
Game manipulation stuff.

Created May 11, 2024

@author montreal91
"""
from core.game_repostory import GameRepository
from core.game import Game


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
        game = self._game_repository.get_game(game_id)

    def get_main_screen_info(self, game_id, manager_club_id):
        game = self._game_repository.get_game(game_id)
        context = game.get_context(manager_club_id)

        info = {}
        info["day"] = context["day"]
        info["balance"] = context["balance"]
        info["club_name"] = context["club_name"]

        return info

    def get_player_list_info(self, game_id, manager_club_id):
        context = self._game_repository.get_game(game_id).get_context(
            manager_club_id
        )
        info = {"players": []}

        player_slot_stuff = context["user_players"]

        for i, player in enumerate(player_slot_stuff):
            info["players"].append(self._player_to_row_dict(
                player.player,
                i,
                player.is_selected,
                player.coach_level
            ))

        info["practice_cost"] = context["practice_cost"]

        return info

    def _player_to_row_dict(self, player, player_id, is_selected, coach_level):
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

        return plr
