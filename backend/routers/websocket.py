"""WebSocket 路由：房间内实时通信"""
import asyncio
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core import ai_bot
from core.game_state import Room, get_room

router = APIRouter()

# room_id -> player_id -> WebSocket
CONNECTIONS: dict = {}


async def _send(ws: WebSocket, payload: dict):
    try:
        await ws.send_text(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass


async def broadcast(room: Room, payload: dict):
    for ws in list(CONNECTIONS.get(room.id, {}).values()):
        await _send(ws, payload)


async def sync_room(room: Room):
    """全量状态广播 + 事件广播"""
    data = room.game.to_dict()
    data["players"] = room.players_info()
    data["mode"] = room.mode
    await broadcast(room, {"type": "sync", "data": data})
    for ev in room.game.drain_events():
        await broadcast(room, {"type": "event", "data": ev})


async def ai_turn_loop(room: Room):
    """AI 回合：掷骰 -> 展示 -> 行动（带防重入与防死循环保护）"""
    game = room.game
    if getattr(room, "_ai_running", False):
        return
    room._ai_running = True
    try:
        while room.mode == "ai" and not game.winner and game.current_turn == "W":
            await asyncio.sleep(0.8)
            # sleep 期间回合可能已变化（如玩家极速操作），必须重新校验
            if get_room(room.id) is not room or game.winner or game.current_turn != "W":
                return
            if game.turn_phase == "roll":
                game.roll_dice()
                odd = game.dice_value % 2 == 1
                game.emit(f"🎲 AI 掷出 {game.dice_value} 点（{'单数落子' if odd else '双数抽卡'}）", "dice")
                if game.drawn_card:
                    game.emit(f"🃏 AI 抽到技能卡【{game.drawn_card}】", "card")
                await sync_room(room)
                await asyncio.sleep(1.6)  # 等待前端骰子动画
                if game.winner or game.current_turn != "W":
                    return
            before = game.step_count
            ai_bot.ai_act(game, "W")
            if game.step_count == before and game.current_turn == "W":
                # AI 无法行动（极端情况）：跳过回合，防止死循环
                game.emit("AI 无法行动，跳过回合", "info")
                game.end_turn()
            await sync_room(room)
            await asyncio.sleep(0.4)
    finally:
        room._ai_running = False


async def maybe_ai(room: Room):
    if room.mode == "ai" and not room.game.winner and room.game.current_turn == "W":
        asyncio.create_task(ai_turn_loop(room))


async def handle_action(room: Room, player_id: str, mtype: str, data: dict, ws: WebSocket):
    game = room.game
    player = room.players[player_id]
    color = player.color

    async def err(code, msg):
        await _send(ws, {"type": "error", "data": {"code": code, "msg": msg}})

    if game.winner:
        await err("GAME_OVER", "对局已结束")
        return
    if color != game.current_turn:
        await err("NOT_YOUR_TURN", "还没轮到你行动")
        return

    if mtype == "roll":
        if game.roll_dice():
            odd = game.dice_value % 2 == 1
            game.emit(f"🎲 {player.name} 掷出 {game.dice_value} 点（{'单数落子' if odd else '双数抽卡'}）", "dice")
            if game.drawn_card:
                game.emit(f"🃏 抽到技能卡【{game.drawn_card}】，本回合可额外使用一次", "card")
            await sync_room(room)
        else:
            await err("BAD_PHASE", "当前不能掷骰")
    elif mtype == "move":
        try:
            x, y = int(data.get("x")), int(data.get("y"))
        except (TypeError, ValueError):
            await err("BAD_MOVE", "坐标非法")
            return
        result = game.apply_move(color, x, y)
        if not result.get("ok"):
            await err("BAD_MOVE", result.get("msg", "落子失败"))
            return
        await sync_room(room)
        await maybe_ai(room)
    elif mtype == "skill":
        result = game.apply_skill(
            color,
            data.get("skill_name"),
            data.get("target_x"),
            data.get("target_y"),
            data.get("extra"),
        )
        if not result.get("ok"):
            await err("BAD_SKILL", result.get("msg", "技能释放失败"))
            return
        await sync_room(room)
        await maybe_ai(room)
    else:
        await err("UNKNOWN", "未知消息类型")


@router.websocket("/ws/room/{room_id}/{player_id}")
async def ws_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    room = get_room(room_id)
    if not room or player_id not in room.players:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    CONNECTIONS.setdefault(room.id, {})[player_id] = websocket
    player = room.players[player_id]
    was_offline = not player.connected
    player.connected = True
    player.disconnected_at = None
    room.touch()
    if was_offline:
        room.game.emit(f"{player.name} 重新连接", "info")
    await sync_room(room)
    try:
        while True:
            raw = await websocket.receive_text()
            room.touch()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "data": {"code": "BAD_JSON", "msg": "消息格式错误"}})
                continue
            mtype = msg.get("type")
            if mtype == "ping":
                await _send(websocket, {"type": "pong"})
                continue
            try:
                await handle_action(room, player_id, mtype, msg.get("data") or {}, websocket)
            except Exception as e:  # noqa: BLE001
                await _send(websocket, {"type": "error", "data": {"code": "SERVER", "msg": f"服务器错误: {e}"}})
    except WebSocketDisconnect:
        pass
    finally:
        CONNECTIONS.get(room.id, {}).pop(player_id, None)
        player.connected = False
        player.disconnected_at = time.time()
        await broadcast(room, {"type": "event", "data": {"msg": f"{player.name} 断开了连接", "type": "info"}})