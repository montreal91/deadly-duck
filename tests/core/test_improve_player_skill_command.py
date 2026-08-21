from core.club import Club
from core.player import Player
from core.player import level_exp
from core.ports.inbound.commands.improve_player_skill_command import (
    ImprovePlayerSkillCommand,
)
from core.ports.inbound.commands.improve_player_skill_command import (
    ImprovePlayerSkillCommandHandler,
)


def test_improve_player_skill_command_improves_player_and_saves_game():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1) + level_exp(2))
    club = _make_club(player)
    game = _Game(clubs={"club": club})
    game_repository = _GameRepository(game)
    club_provider = _ClubProvider()
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={
            "technique": 1,
            "endurance": 1,
        },
    ))

    assert result.success
    assert player.technique == 55
    assert player.endurance == 45
    assert player.skill_points == 0
    assert game_repository.saved_game is game
    assert club_provider.saved_clubs == [club]


def test_improve_player_skill_command_rejects_invalid_skill_key():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    game_repository = _GameRepository(_Game(clubs={"club": club}))
    club_provider = _ClubProvider()
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={"volley": 1},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    assert game_repository.saved_game is None
    assert club_provider.saved_clubs is None


def test_improve_player_skill_command_rejects_negative_skill_points():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    game_repository = _GameRepository(_Game(clubs={"club": club}))
    club_provider = _ClubProvider()
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={"technique": -1},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    assert game_repository.saved_game is None
    assert club_provider.saved_clubs is None


def test_improve_player_skill_command_rejects_overspending():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    game_repository = _GameRepository(_Game(clubs={"club": club}))
    club_provider = _ClubProvider()
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="club",
        player_id=player.player_id,
        skill_points={"technique": 2},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    assert game_repository.saved_game is None
    assert club_provider.saved_clubs is None


def test_improve_player_skill_command_rejects_player_from_wrong_club():
    player = Player(technique=50, endurance=40)
    player.add_experience(level_exp(1))
    club = _make_club(player)
    wrong_club = Club(
        club_id="wrong-club",
        game_id="game",
        name="Wrong Club",
        coach_power=1,
    )
    game_repository = _GameRepository(_Game(clubs={
        "club": club,
        "wrong-club": wrong_club,
    }))
    club_provider = _ClubProvider()
    handler = ImprovePlayerSkillCommandHandler(
        game_repository,
        club_provider,
    )

    result = handler(ImprovePlayerSkillCommand(
        game_id="game",
        club_id="wrong-club",
        player_id=player.player_id,
        skill_points={"technique": 1},
    ))

    assert not result.success
    assert player.technique == 50
    assert player.endurance == 40
    assert player.skill_points == 1
    assert game_repository.saved_game is None
    assert club_provider.saved_clubs is None


def _make_club(player):
    club = Club(
        club_id="club",
        game_id="game",
        name="Club",
        coach_power=1,
    )
    club.add_player(player)
    return club


class _Game:
    def __init__(self, clubs):
        self.clubs = clubs


class _GameRepository:
    def __init__(self, game):
        self._game = game
        self.saved_game = None

    def get_game(self, _game_id):
        return self._game

    def save_game(self, game):
        self.saved_game = game


class _ClubProvider:
    def __init__(self):
        self.saved_clubs = None

    def save_clubs(self, clubs):
        self.saved_clubs = list(clubs)
