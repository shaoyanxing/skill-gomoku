"""调试五子判定"""
import sys
sys.path.insert(0, "/home/pi/skill-gomoku/backend")
from core.skills import count_line, has_five, BOARD_SIZE

board = [[""] * BOARD_SIZE for _ in range(BOARD_SIZE)]
for i in range(5):
    board[7][7+i] = "B"

# 打印棋盘
for y in range(6, 9):
    row = "".join(board[y][x] if board[y][x] else "." for x in range(5, 15))
    print(f"Row {y}: {row}")

# 测试 count_line
for x in range(7, 12):
    r = count_line(board, 7, x, 1, 0, "B")
    l = count_line(board, 7, x, -1, 0, "B")
    total = 1 + r + l
    print(f"  (7,{x}): right={r} left={l} total={total} five={has_five(board, 7, x, 'B')}")
