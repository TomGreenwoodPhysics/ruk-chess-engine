# Benchmark Log

This file records reproducible benchmark results for Bitfish. Results are intended as relative progress markers rather than absolute Elo ratings.

## 2026-06-08 — Bitfish C++ persistent UCI benchmark

### Engine

* Engine: Bitfish C++
* Mode: persistent UCI process
* Fresh engine each move: false
* Time per move: 0.50 s
* Maximum depth cap: 100
* Build: C++20, `-O2`
* Transposition table: enabled
* TT hit reporting: enabled through UCI `tbhits`

### Opponent

* Opponent: Stockfish
* Stockfish strength setting: 2250 Elo
* Stockfish time per move: 0.10 s

### Match settings

* Games requested: 50
* Games completed: 50
* Unfinished games: 0
* Maximum plies per game: 400
* Colours alternated between games

### Result

| Result type                                   |     Count |
| --------------------------------------------- | --------: |
| Wins                                          |        25 |
| Draws                                         |        11 |
| Losses                                        |        14 |
| Score                                         | 30.5 / 50 |
| Score rate                                    |     61.0% |
| Estimated Elo difference vs Stockfish setting |       +78 |

Approximate benchmark rating under these conditions:

```text
2250 + 78 ≈ 2328
```

This should be treated as a benchmark-specific estimate, not an official Elo rating.

### Search statistics

| Metric                   |   Value |
| ------------------------ | ------: |
| Engine moves analysed    |    2248 |
| Average depth reached    |    9.30 |
| Maximum depth reached    |      22 |
| Average nodes per move   | 233,839 |
| Average time per move    |  0.50 s |
| Average nodes/s          | 463,940 |
| Average legal moves      |    29.7 |
| Average TT hits per move |  20,564 |

Average depth by phase:

| Phase      | Average depth |
| ---------- | ------------: |
| Opening    |          7.91 |
| Middlegame |          8.89 |
| Endgame    |         12.09 |

### Stability notes

The benchmark completed all 50 games with no unfinished games, no illegal move crashes, and no UCI process desynchronisation.

This run used persistent UCI mode, meaning the engine was not restarted between moves. This is closer to normal engine usage than the earlier fresh-process benchmark setup.

### Notes

The average score diagnostic is currently distorted by mate scores such as `999999` and `-999998`, so it should not be used as a reliable measure of average positional evaluation.

Future benchmark logs should include median score or average non-mate score instead.

### Output files

The benchmark script wrote:

```text
analysis_games/bitfish_cpp_benchmark_games.pgn
analysis_games/bitfish_cpp_move_log.jsonl
analysis_games/bitfish_cpp_diagnostics.csv
```

These files contain the full PGN record, per-move JSON logs, and diagnostics CSV for deeper analysis.
