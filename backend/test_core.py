"""快速测试核心逻辑"""
import sys
sys.path.insert(0, "/home/pi/skill-gomoku/backend")

from core.skills import SkillEngine, has_five, find_live_three
from core.game_state import GameState

# 1. 初始状态
state = GameState(mode="pve")
assert state.board[7][7] == ""
print("1. 初始状态: OK")

# 2. 五子判定
for i in range(5):
    state.board[7][7+i] = "B"
assert has_five(state.board, 7, 7, "B")  # (x=7, y=7) 是第一颗子的位置
print("2. 五子判定: OK")

# 3. 活三检测
state2 = GameState()
for i in range(3):
    state2.board[7][4+i] = "W"
state2.board[7][3] = ""
state2.board[7][7] = ""
live = find_live_three(state2.board, "W")
print(f"3. 活三检测: {len(live)} 个活三")

# 4. 排山倒海
state3 = GameState()
state3.board[7][7] = "B"
state3.board[7][8] = "W"
board = [row[:] for row in state3.board]
board2, moved, warn = SkillEngine._pai_shan_dao_hai(board, "B")
assert moved > 0
print(f"4. 排山倒海: 移动 {moved} 子 OK")

# 5. 落子
state4 = GameState(mode="pve")
err = state4.place_piece(7, 7)
assert err is None
assert state4.board[7][7] == "B"
print(f"5. 落子: OK (当前回合: {state4.current_turn})")

print("\n✅ 全部核心测试通过！")
