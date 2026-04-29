import json
import os

DATA_FILE = "chess_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"saved_game": None, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"saved_game": None, "history": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_game(fen, mode, difficulty=None, player_color=None):
    data = load_data()
    data["saved_game"] = {
        "fen": fen,
        "mode": mode,
        "difficulty": difficulty,
        "player_color": player_color
    }
    save_data(data)

def load_saved_game():
    data = load_data()
    return data.get("saved_game")

def clear_saved_game():
    data = load_data()
    data["saved_game"] = None
    save_data(data)

def add_to_history(result, mode, moves_count):
    data = load_data()
    if "history" not in data:
        data["history"] = []
    data["history"].append({
        "result": result,
        "mode": mode,
        "moves_count": moves_count
    })
    save_data(data)

def get_history():
    data = load_data()
    return data.get("history", [])
