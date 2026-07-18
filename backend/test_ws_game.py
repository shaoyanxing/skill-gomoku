"""测试 WebSocket 连接"""
import sys
sys.path.insert(0, "/home/pi/skill-gomoku/backend")
import asyncio
import json
from core.game_state import GameState, rooms
from models.schemas import SkillName

async def test_ws():
    # 创建房间
    state = GameState(mode="pve", players={"test_player": "B"})
    room_id = state.room_id
    rooms[room_id] = state
    
    # 模拟一次完整的对局：玩家落子 → AI 回应
    print(f"房间: {room_id}")
    print(f"初始步数: {state.step_count}, 回合: {state.current_turn}")
    
    for i in range(10):
        print(f"\n--- 回合 {i+1} ---")
        if state.current_turn == "B":
            # 玩家落子
            x, y = 7 + i, 7 + i
            if x >= 15 or y >= 15:
                x, y = 7, 14 - i
            err = state.place_piece(x, y)
            print(f"玩家落子 ({x},{y}): {'OK' if err is None else err}")
        else:
            # AI
            from core.ai_bot import ai_play
            result = ai_play(state)
            print(f"AI: {result}")
        
        if state.winner:
            print(f"\n🏆 {state.winner} 获胜!")
            break
    
    # 显示棋盘
    print("\n棋盘:")
    for y in range(15):
        row = "".join("●" if state.board[y][x] == "B" else "○" if state.board[y][x] == "W" else "·" for x in range(15))
        print(f"  {row}")
    
    print(f"\n最终步数: {state.step_count}")

asyncio.run(test_ws())
