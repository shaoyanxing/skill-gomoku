"""模拟多步 AI 对弈测试"""
import sys
sys.path.insert(0, "/home/pi/skill-gomoku/backend")

from core.game_state import GameState
from core.ai_bot import ai_play

state = GameState(mode="pve")
state.players = {"player1": "B"}

for step in range(20):
    print(f"\n--- 第 {step} 步 (回合: {state.current_turn}, 步数: {state.step_count}) ---")
    if step % 2 == 0:
        # 模拟玩家落子
        print("玩家落子...")
        err = state.place_piece(7 + step//2, 7 + step//2)
        if err:
            print(f"  玩家错误: {err}")
    else:
        # AI 行动
        print("AI 行动...")
        result = ai_play(state)
        print(f"  AI 操作: {result['type']}", end="")
        if 'skill_name' in result:
            print(f" {result['skill_name']}", end="")
        if 'x' in result:
            print(f" ({result.get('x')},{result.get('y')})", end="")
        print()
    
    if state.winner:
        print(f"\n🏆 {state.winner} 获胜!")
        break
    
    # 打印棋盘
    if state.step_count <= 10 or state.step_count % 5 == 0:
        for y in range(15):
            row = "".join("●" if state.board[y][x] == "B" else "○" if state.board[y][x] == "W" else "·" for x in range(15))
            print(f"  {row}")

print("\n✅ 模拟完成")
