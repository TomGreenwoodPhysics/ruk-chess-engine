import csv
import subprocess
import time
from pathlib import Path

import chess
import chess.engine


ROOT = Path(__file__).resolve().parent

BITFISH_EXE = ROOT / "bitfish_cpp" / "bitfish.exe"
STOCKFISH_PATH = Path(
    r"C:\Users\Tom Greenwood\Desktop\Coding Projects\Chess Bot\stockfish\stockfish-windows-x86-64-avx2.exe"
)

SUITE_DIR = ROOT / "analysis_games" / "weakness_suite_original_stable_200"
EPD_FILE = SUITE_DIR / "stockfish_verified_blunders_top75.epd"
OUT_FILE = SUITE_DIR / "bitfish_weakness_suite_scored_results.csv"

BITFISH_DEPTH = 8
STOCKFISH_DEPTH = 12
TIMEOUT_SECONDS = 10
MATE_SCORE = 100000


def ask_bitfish(fen):
    commands = (
        "uci\n"
        "isready\n"
        f"position fen {fen}\n"
        f"go depth {BITFISH_DEPTH}\n"
        "quit\n"
    )

    start = time.time()

    proc = subprocess.run(
        [str(BITFISH_EXE), "uci"],
        input=commands,
        text=True,
        capture_output=True,
        timeout=TIMEOUT_SECONDS,
    )

    elapsed = time.time() - start
    bestmove = ""
    final_info = ""

    for line in proc.stdout.splitlines():
        line = line.strip()

        if line.startswith("info depth"):
            final_info = line

        if line.startswith("bestmove"):
            parts = line.split()
            if len(parts) >= 2:
                bestmove = parts[1]

    return bestmove, final_info, elapsed


def score_cp(info, pov_colour):
    score = info["score"].pov(pov_colour)

    if score.is_mate():
        mate = score.mate()
        if mate is None:
            return 0
        return MATE_SCORE if mate > 0 else -MATE_SCORE

    return score.score(mate_score=MATE_SCORE)


def analyse_cp(engine, board, pov_colour):
    info = engine.analyse(board, chess.engine.Limit(depth=STOCKFISH_DEPTH))
    return score_cp(info, pov_colour)


def stockfish_best_move(engine, board):
    result = engine.play(board, chess.engine.Limit(depth=STOCKFISH_DEPTH))
    return result.move


def safe_push(board, move_text):
    try:
        move = chess.Move.from_uci(move_text)
    except ValueError:
        return None

    if move not in board.legal_moves:
        return None

    board.push(move)
    return move


def main():
    if not BITFISH_EXE.exists():
        raise FileNotFoundError(f"missing engine: {BITFISH_EXE}")

    if not STOCKFISH_PATH.exists():
        raise FileNotFoundError(f"missing Stockfish: {STOCKFISH_PATH}")

    if not EPD_FILE.exists():
        raise FileNotFoundError(f"missing suite: {EPD_FILE}")

    fens = [
        line.strip()
        for line in EPD_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows = []
    matched_stockfish = 0
    total_eval_loss = 0
    legal_positions = 0

    print(f"testing {len(fens)} positions")

    with chess.engine.SimpleEngine.popen_uci(str(STOCKFISH_PATH)) as sf:
        for index, fen in enumerate(fens, start=1):
            board = chess.Board(fen)
            pov_colour = board.turn

            print(f"[{index}/{len(fens)}] ", end="", flush=True)

            try:
                bitfish_move, final_info, elapsed = ask_bitfish(fen)

                sf_move = stockfish_best_move(sf, board)

                sf_best_board = board.copy()
                sf_best_board.push(sf_move)
                sf_eval_after_best = analyse_cp(sf, sf_best_board, pov_colour)

                bitfish_board = board.copy()
                parsed_bitfish_move = safe_push(bitfish_board, bitfish_move)

                if parsed_bitfish_move is None:
                    bitfish_eval_after = ""
                    eval_loss = ""
                    matched = False
                    legal = False
                else:
                    bitfish_eval_after = analyse_cp(sf, bitfish_board, pov_colour)
                    eval_loss = sf_eval_after_best - bitfish_eval_after
                    matched = parsed_bitfish_move == sf_move
                    legal = True

                    legal_positions += 1
                    total_eval_loss += eval_loss
                    if matched:
                        matched_stockfish += 1

                print(f"Bitfish {bitfish_move}, SF {sf_move}, loss {eval_loss}")

                rows.append({
                    "index": index,
                    "fen": fen,
                    "bitfish_move": bitfish_move,
                    "stockfish_best_move": str(sf_move),
                    "matched_stockfish_best": matched,
                    "stockfish_eval_after_best": sf_eval_after_best,
                    "stockfish_eval_after_bitfish": bitfish_eval_after,
                    "eval_loss_cp": eval_loss,
                    "bitfish_legal": legal,
                    "elapsed_seconds": f"{elapsed:.3f}",
                    "bitfish_final_info": final_info,
                })

            except Exception as exc:
                print(f"ERROR: {exc}")

                rows.append({
                    "index": index,
                    "fen": fen,
                    "bitfish_move": "ERROR",
                    "stockfish_best_move": "",
                    "matched_stockfish_best": False,
                    "stockfish_eval_after_best": "",
                    "stockfish_eval_after_bitfish": "",
                    "eval_loss_cp": "",
                    "bitfish_legal": False,
                    "elapsed_seconds": "",
                    "bitfish_final_info": str(exc),
                })

    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "fen",
                "bitfish_move",
                "stockfish_best_move",
                "matched_stockfish_best",
                "stockfish_eval_after_best",
                "stockfish_eval_after_bitfish",
                "eval_loss_cp",
                "bitfish_legal",
                "elapsed_seconds",
                "bitfish_final_info",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    average_loss = total_eval_loss / legal_positions if legal_positions else 0

    print()
    matched_count = sum(
        1 for row in rows
        if row["bitfish_move"] == row["stockfish_best_move"]
    )

    losses = [int(row["eval_loss_cp"]) for row in rows]

    normal_losses = [
        loss for loss in losses
        if abs(loss) < 90000
    ]

    average_loss = sum(losses) / len(losses)
    normal_average_loss = sum(normal_losses) / len(normal_losses)

    print()
    print(f"matched Stockfish best: {matched_count}/{len(rows)}")
    print(f"average eval loss: {average_loss:.1f} cp")
    print(f"normal-only average eval loss: {normal_average_loss:.1f} cp")
    print(f"normal positions counted: {len(normal_losses)}/{len(rows)}")


if __name__ == "__main__":
    main()
