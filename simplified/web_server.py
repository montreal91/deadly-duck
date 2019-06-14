
"""
Created Apr 21, 2019

@author montreal91
"""

import time

from multiprocessing import Queue

from flask import Flask
from flask import json
from flask import jsonify
from flask import render_template
from flask import request
from flask_socketio import SocketIO
from flask_socketio import emit

from simplified.encoder import DduckJsonEncoder
from simplified.game_server import DdGameAction
from simplified.game_server import DdGameServer
from simplified.match import CalculateConstExhaustion
from simplified.match import LinearProbabilityFunction
from simplified.player import DdPlayerReputationCalculator
from simplified.player import ExhaustedLinearRecovery


app = Flask(__name__)
app.json_encoder = DduckJsonEncoder


in_queue = Queue()
out_queue = Queue()
game_server = DdGameServer(in_queue, out_queue)
game_server.start()

socket = SocketIO()
socket.init_app(app, json=json)


def Emitter():
    while True:
        time.sleep(0.5)
        if out_queue.empty():
            continue
        msg = out_queue.get(False)
        for pk, context in msg.items():
            socket.emit("context", context, namespace="/tennis/")


socket.start_background_task(Emitter)


@app.route("/")
def Index():
    return render_template("index.html")


@app.route("/api/next_day/", methods=["POST"])
def NextDay():
    print(type(request.json["pk"]))
    action = DdGameAction(
        type="next_day",
        pk=request.json["pk"],
        arguments={},
    )
    in_queue.put(action)
    return jsonify(ok=True)


@app.route("/api/start_new_game/", methods=["POST"])
def StartNewGame():
    action = DdGameAction(
        type="start_new_game",
        pk=request.json["pk"],
        arguments=dict(
            exdiv_matches=2,
            exhaustion_function=CalculateConstExhaustion,
            exhaustion_per_set=2,
            indiv_matches=2,
            probability_function=LinearProbabilityFunction,
            recovery_day=4,
            recovery_function=ExhaustedLinearRecovery,
            playoff_clubs=8,
            reputation_function=DdPlayerReputationCalculator(6, 5),
            starting_club=0,
        ),
    )
    in_queue.put(action)
    return jsonify(ok=True)