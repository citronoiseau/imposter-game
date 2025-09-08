from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_caching import Cache
from uuid import uuid4
from random import randint, shuffle
from data.game_info import GameInfo, Player, GameState

# ------------------------
# Setup
# ------------------------
app = Flask(__name__)
CORS(app)

# Cache setup (store game state)
config = {
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,  # keep a game around for 24 hours
    "CACHE_THRESHOLD": 10000,
    "CACHE_DIR": "/tmp",
}
app.config.from_mapping(config)
game_cache = Cache(app)

socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# ------------------------
# Utilities
# ------------------------
def rand_xyz() -> str:
    a, z = ord("a"), ord("z")
    return "".join(chr(randint(a, z)) for _ in range(3))

# ------------------------
# Socket.IO Events
# ------------------------

@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on("create_game")
def handle_create_game(data):
    while True:
        game_id = f"{rand_xyz()}-{rand_xyz()}-{rand_xyz()}"
        if not game_cache.get(game_id):
            break

    game = GameInfo(
        id=game_id,
        players={},
        imposters=data.get("imposters", 1),
        inn_question=data.get("innocent_question", ""),
        imp_question=data.get("imposter_question", "")
    )
    game_cache.set(game_id, game)
    emit("game_created", {"game_id": game_id})

@socketio.on("join_game")
def handle_join_game(data):
    game_id = data.get("game_id")
    player_name = data.get("name", "Player")

    game = game_cache.get(game_id)
    if not game:
        emit("error", {"message": "Game not found"})
        return

    player_id = str(uuid4())
    player = Player(
        id=player_id,
        name=player_name,
        is_imposter=False,
        sid=request.sid
    )

    game.players[player_id] = player
    game_cache.set(game_id, game)

    join_room(game_id)

    emit("player_joined", {"player_id": player_id, "name": player_name}, to=game_id)

@socketio.on("start_game")
def handle_start_game(data):
    game_id = data.get("game_id")
    game = game_cache.get(game_id)

    if not game:
        emit("error", {"message": "Game not found"})
        return

    player_list = list(game.players.values())
    shuffle(player_list)

    for i, p in enumerate(player_list):
        p.is_imposter = (i < game.imposters)

    game_cache.set(game_id, game)

    for p in player_list:
        role = "imposter" if p.is_imposter else "innocent"
        question = game.imp_question if p.is_imposter else game.inn_question
        emit("role_assigned", {"role": role, "question": question}, room=p.sid)

    emit("game_started", {"imposters": game.imposters}, to=game_id)

@socketio.on("push_game_state")
def handle_push_game_state(data):
    game_id = data.get("game_id")
    game: GameInfo = game_cache.get(game_id)

    if not game:
        emit("error", {"message": "Game not found"})
        return

    new_state = game.next_state()
    game_cache.set(game_id, game)

    emit("game_state_updated", {"current_state": new_state}, to=game_id)