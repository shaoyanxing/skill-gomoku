"""Pydantic 数据模型与技能枚举"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SkillName(str, Enum):
    # 位移类
    PAI_SHAN_DAO_HAI = "排山倒海"
    FEI_SHA_ZOU_SHI = "飞沙走石"
    YI_HUA_JIE_MU = "移花接木"      # 全局1次
    LI_BA_SHAN_XI = "力拔山兮"
    BO_YUN_JIAN_RI = "拨云见日"
    # 凝结类
    JING_RU_ZHI_SHUI = "静如止水"
    BING_DONG_SAN_CHI = "冰冻三尺"
    BU_DONG_RU_SHAN = "不动如山"
    # 阴阳类
    WU_WEI_ER_ZHI = "无为而治"      # 全局1次
    AN_DU_CHEN_CANG = "暗渡陈仓"
    ZONG_HENG_TIAN_XIA = "纵横天下"  # 全局2次


class CreateRoomRequest(BaseModel):
    player_name: str = "玩家"
    mode: str = "pvp"  # "pvp" 联机 | "ai" 单机


class CreateRoomResponse(BaseModel):
    room_id: str
    player_id: str
    color: str
    mode: str


class JoinRoomRequest(BaseModel):
    room_id: str
    player_name: str = "玩家"


class JoinRoomResponse(BaseModel):
    room_id: str
    player_id: str
    color: str


class MoveData(BaseModel):
    x: int
    y: int


class SkillData(BaseModel):
    skill_name: SkillName
    target_x: Optional[int] = None
    target_y: Optional[int] = None
    extra: Optional[dict] = None