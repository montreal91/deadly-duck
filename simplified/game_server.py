
"""
Created Apr 20, 2019

@author montreal91
"""

import time

from functools import wraps
from multiprocessing import Process
from multiprocessing import Queue
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple

from app.exceptions import BadUserInputException
from simplified.game import DdGameDuck
from simplified.game import DdGameParams


def Handler(function):
    @wraps(function)
    def Wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except AssertionError as e:
            raise BadUserInputException(e.message)
    return Wrapper


class _DdServerSlot:
    game: DdGameDuck
    time_since_last_update: int = 0


class DdGameAction(NamedTuple):
    arguments: Dict[str, Any]
    pk: str
    type: str


class DdGameServer(Process):
    """
    Process-based game server.

    It runs its loop, updating different game instances in a separate process.
    """
    _action_handlers: Dict[str, Callable]
    _in_queue: Queue
    _is_running: bool = True
    _max_time: float = 600.0
    _out_queue: Queue
    _slots: Dict[str, _DdServerSlot]
    _tick: float = 0.5

    def __init__(self, in_queue: Queue, out_queue: Queue):
        super().__init__()
        self._action_handlers = {}
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._slots = {}

        self._InitActionHandlers()

    def join(self):
        self._is_running = False
        super().join()

    def run(self):
        print("Game server is running.")
        try:
            while self._is_running:
                time.sleep(self._tick)
                self._ProcessActions()
                self._Update()
                self._Emit()
        except KeyboardInterrupt:
            print("Game server is stopped.")
            self._is_running = False

    def _DispatchAction(self, action: DdGameAction):
        if action.type not in self._action_handlers:
            raise Exception
        print(action)
        self._action_handlers[action.type](action)

    def _Emit(self):
        msg = {}
        for pk in self._slots:
            msg[pk] = self._slots[pk].game.context

        self._out_queue.put(msg)

    def _GetActions(self) -> List[DdGameAction]:
        actions = []
        while not self._in_queue.empty():
            actions.append(self._in_queue.get(False))
        return actions

    def _InitActionHandlers(self):
        self._action_handlers["load_game"] = self._HandleLoadGame
        self._action_handlers["next_day"] = self._HandleNextDay
        self._action_handlers["save_and_quit"] = self._HandleSaveAndQuit
        self._action_handlers["select_player"] = self._HandleSelectPlayer
        self._action_handlers["set_practice"] = self._HandleSetPractice
        self._action_handlers["start_new_game"] = self._HandleStartNewGame

    def _ProcessActions(self):
        for action in self._GetActions():
            self._DispatchAction(action)

    def _SaveGame(self, pk: str):
        pass

    def _Update(self):
        to_pop = []
        for pk, slot in self._slots.items():
            slot.time_since_last_update += self._tick
            if slot.time_since_last_update > self._max_time:
                self._SaveGame(pk)
                to_pop.append(pk)

        for pk in to_pop:
            self._slots.pop(pk)

    # Action handlers
    @Handler
    def _HandleLoadGame(self, action: DdGameAction):
        pass

    @Handler
    def _HandleNextDay(self, action: DdGameAction):
        self._slots[action.pk].game.Update()

    @Handler
    def _HandleSaveAndQuit(self, action: DdGameAction):
        pass

    @Handler
    def _HandleSelectPlayer(self, action: DdGameAction):
        self._slots[action.pk].game.SelectPlayer(action.arguments["player"])

    @Handler
    def _HandleSetPractice(self, action: DdGameAction):
        self._slots[action.pk].game.SetPractice(*action.arguments["practice"])

    @Handler
    def _HandleStartNewGame(self, action: DdGameAction):
        if action.pk in self._slots:
            self._SaveGame(action.pk)

        params = DdGameParams(**action.arguments)
        new_game = DdGameDuck(params)
        slot = _DdServerSlot()
        slot.game = new_game
        self._slots[action.pk] = slot
