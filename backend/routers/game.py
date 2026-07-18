"""REST API：房间管理"""
from fastapi import APIRouter, HTTPException

from core.game_state import create_room, get_room
from models.schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
)

router = APIRouter(prefix="/api/room", tags=["room"])


@router.post("/create", response_model=CreateRoomResponse)
def create(req: CreateRoomRequest):
    mode = req.mode if req.mode in ("pvp", "ai") else "pvp"
    room = create_room(mode)
    player = room.add_player(req.player_name)
    return CreateRoomResponse(
        room_id=room.id, player_id=player.id, color=player.color, mode=mode
    )


@router.post("/join", response_model=JoinRoomResponse)
def join(req: JoinRoomRequest):
    room = get_room(req.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在或已销毁")
    if room.mode == "ai":
        raise HTTPException(status_code=400, detail="该房间为单机对局，无法加入")
    if room.is_full():
        raise HTTPException(status_code=409, detail="房间已满")
    player = room.add_player(req.player_name)
    return JoinRoomResponse(room_id=room.id, player_id=player.id, color=player.color)