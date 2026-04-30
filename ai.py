import chess
import chess.engine
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_engine_path():
    if sys.platform == "win32":
        return resource_path(os.path.join("assets", "engine", "stockfish.exe"))
    return resource_path(os.path.join("assets", "engine", "stockfish"))

def get_ai_move(board, difficulty):
    engine_path = get_engine_path()
    if not os.path.exists(engine_path):
        return list(board.legal_moves)[0] if list(board.legal_moves) else None

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        limit = chess.engine.Limit(time=0.1)
        if difficulty == 1:
            engine.configure({"Skill Level": 0})
        elif difficulty == 2:
            engine.configure({"Skill Level": 5})
        else:
            engine.configure({"Skill Level": 15})
            limit = chess.engine.Limit(time=0.5)

        result = engine.play(board, limit)
        return result.move

def evaluate_move_quality(board, move):
    engine_path = get_engine_path()
    if not os.path.exists(engine_path):
        return "good"

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        info_before = engine.analyse(board, chess.engine.Limit(depth=10))
        score_before = info_before["score"].white().score(mate_score=10000)

        board.push(move)
        info_after = engine.analyse(board, chess.engine.Limit(depth=10))
        score_after = info_after["score"].white().score(mate_score=10000)
        board.pop()

        is_white_turn = board.turn == chess.WHITE

        if is_white_turn:
            diff = score_after - score_before
        else:
            diff = score_before - score_after

        if diff >= 50:
            return "brilliant"
        elif diff >= 10:
            return "great"
        elif diff >= -20:
            return "best"
        elif diff <= -300:
            return "blunder"
        elif diff <= -100:
            return "mistake"
        elif diff <= -50:
            return "inaccuracy"

        return "good"
