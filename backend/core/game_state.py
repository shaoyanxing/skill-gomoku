"""游戏状态类与房间管理（内存存储）"""
import random
import time
import uuid
from typing import Dict, List, Optional

from models.schemas import SkillName
from core import skills as se

COLOR_NAME = {"B": "黑", "W": "白"}


class GameState:
    def __init__(self):
        self.board = [["" for _ in range(se.BOARD_SIZE)] for _ in range(se.BOARD_SIZE)]
        self.current_turn = "B"
        self.step_count = 0
        self.warnings = {"B": 0, "W": 0}
        self.skill_usage = {"B": {s.value: se.SKILL_LIMITS[s] for s in SkillName}, "W": {s.value: se.SKILL_LIMITS[s] for s in SkillName}}  # 全部已用完，靠抽卡获得临时次数
        self.bonus_uses = {"B": {}, "W": {}}        # 抽卡获得的临时次数（当回合有效）
        self.frozen_zones: List[dict] = []
        self.ban_zones: List[dict] = []
        self.peace_until_step = 0
        self.immune = {"B": 0, "W": 0}              # 不动如山 -> 免疫截止步数
        self.skill_ban = {"B": 0, "W": 0}           # 静如止水/纵横天下 -> 封印截止步数
        self.last_move: Optional[List[int]] = None
        self.winner = ""
        self.win_reason = ""
        # 骰子机制
        self.dice_value: Optional[int] = None
        self.turn_phase = "roll"                    # roll | move | skill | move_or_skill
        self.drawn_card: Optional[str] = None
        self.events: List[dict] = []

    # ---------------------------------------------------------- 工具
    def emit(self, msg: str, etype: str = "info"):
        self.events.append({"msg": msg, "type": etype})

    def drain_events(self) -> List[dict]:
        ev, self.events = self.events, []
        return ev

    def is_immune(self, color: str) -> bool:
        return self.step_count < self.immune.get(color, 0)

    def is_silenced(self, color: str) -> bool:
        return self.step_count < self.skill_ban.get(color, 0)

    def peace_active(self) -> bool:
        return self.step_count < self.peace_until_step

    def peace_rounds(self) -> int:
        if not self.peace_active():
            return 0
        return (self.peace_until_step - self.step_count + 1) // 2

    def is_frozen(self, x: int, y: int) -> bool:
        return any(
            z["expire_step"] > self.step_count and abs(z["x"] - x) <= 1 and abs(z["y"] - y) <= 1
            for z in self.frozen_zones
        )

    def is_banned(self, x: int, y: int) -> bool:
        return any(
            z["expire_step"] > self.step_count and z["x"] == x and z["y"] == y
            for z in self.ban_zones
        )

        return self.step_count > 0 and self.step_count % 5 == 0

    # ---------------------------------------------------------- 技能次数
    def remaining(self, color: str, name) -> int:
        key = name.value if isinstance(name, SkillName) else name
        base = se.SKILL_LIMITS[SkillName(key)] - self.skill_usage[color].get(key, 0)
        return base + self.bonus_uses[color].get(key, 0)

    def skills_remaining(self, color: str) -> Dict[str, int]:
        return {s.value: self.remaining(color, s) for s in SkillName}

    def has_any_skill(self, color: str) -> bool:
        return any(v > 0 for v in self.skills_remaining(color).values())

    def _consume(self, color: str, skill: SkillName):
        key = skill.value
        if self.bonus_uses[color].get(key, 0) > 0:
            self.bonus_uses[color][key] -= 1
        else:
            self.skill_usage[color][key] = self.skill_usage[color].get(key, 0) + 1

    # ---------------------------------------------------------- 骰子
    def draw_card(self, color: str) -> Optional[str]:
        # 所有技能都可抽，不限制次数
        pool = list(SkillName)
        card = random.choice(pool)
        self.bonus_uses[color][card.value] = self.bonus_uses[color].get(card.value, 0) + 1
        return card.value

    def roll_dice(self) -> bool:
        if self.turn_phase != "roll" or self.winner:
            return False
        self.dice_value = random.randint(1, 6)
        odd = self.dice_value % 2 == 1
        if not odd:
            self.drawn_card = self.draw_card(self.current_turn)
        self.turn_phase = "move" if odd else "move_or_skill"
        return True

    # ---------------------------------------------------------- 落子
    def apply_move(self, color: str, x: int, y: int) -> dict:
        if self.winner:
            return {"ok": False, "msg": "对局已结束"}
        if color != self.current_turn:
            return {"ok": False, "msg": "还没轮到你"}
        if self.turn_phase == "roll":
            return {"ok": False, "msg": "请先掷骰 🎲"}
        if not se.in_board(x, y) or self.board[y][x]:
            return {"ok": False, "msg": "该位置不可落子"}
        if self.is_frozen(x, y):
            return {"ok": False, "msg": "该区域被冰冻三尺冻结！"}
        if self.is_banned(x, y):
            return {"ok": False, "msg": "该点位本回合被飞沙走石封锁！"}
        self.board[y][x] = color
        self.last_move = [x, y]
        self.emit(f"{COLOR_NAME[color]}方落子 ({x},{y})", "info")
        if se.check_five(self.board, x, y, color):
            self.winner = color
            self.win_reason = "五子连珠！"
            self.emit(f"{COLOR_NAME[color]}方五子连珠，获得胜利！", "win")
        self.end_turn()
        return {"ok": True}

    # ---------------------------------------------------------- 技能
    def apply_skill(self, color: str, name, tx=None, ty=None, extra=None) -> dict:
        if self.winner:
            return {"ok": False, "msg": "对局已结束"}
        if color != self.current_turn:
            return {"ok": False, "msg": "还没轮到你"}
        try:
            skill = SkillName(name)
        except ValueError:
            return {"ok": False, "msg": "未知技能"}
        if self.turn_phase == "roll":
            return {"ok": False, "msg": "请先掷骰 🎲"}
        if self.turn_phase == "move":
            return {"ok": False, "msg": "骰子为单数：本回合只能落子"}
        if self.peace_active() and skill != SkillName.WU_WEI_ER_ZHI:
            return {"ok": False, "msg": "无为而治生效中，所有技能被禁用"}
        if self.is_silenced(color):
            return {"ok": False, "msg": "你的技能被封印，本回合无法使用"}
        if self.remaining(color, skill) <= 0:
            return {"ok": False, "msg": "该技能次数已用尽"}
        opp = se.opponent(color)
        # 不动如山：反制对手凝结技 -> 对手记犯规
        if se.SKILL_CATEGORY[skill] == "freeze" and self.is_immune(opp):
            self._consume(color, skill)
            self.add_warning(color, "强行动用凝结技被【不动如山】反噬")
            self.end_turn()
            return {"ok": True, "countered": True}
        result = se.DISPATCH[skill](self, color, tx, ty, extra or {})
        if not result.get("ok"):
            if result.get("foul"):
                self._consume(color, skill)
                self.add_warning(color, result.get("msg", "技能犯规"))
                self.end_turn()
                return {"ok": True, "fouled": True}
            return {"ok": False, "msg": result.get("msg", "技能释放失败")}
        self._consume(color, skill)
        self.emit(f"{COLOR_NAME[color]}方释放【{skill.value}】", "skill")
        if result.get("msg"):
            self.emit(result["msg"], "skill")
        # 技能后的胜负检查
        if se.has_five(self.board, color):
            self.winner = color
            self.win_reason = "技能造就五子连珠！"
            self.emit(f"{COLOR_NAME[color]}方五子连珠，获得胜利！", "win")
        elif se.has_five(self.board, opp):
            self.winner = opp
            self.win_reason = "技能意外成就了对手的五子连珠…"
            self.emit(f"{COLOR_NAME[opp]}方五子连珠，获得胜利！", "win")
        self.end_turn()
        result["ok"] = True
        return result

    def add_warning(self, color: str, msg: str):
        self.warnings[color] += 1
        self.emit(f"⚠️ {COLOR_NAME[color]}方犯规（{self.warnings[color]}/3）：{msg}", "warning")
        if self.warnings[color] >= 3:
            opp = se.opponent(color)
            self.winner = opp
            self.win_reason = "对手三次犯规，判负！"
            self.emit(f"{COLOR_NAME[color]}方三次犯规，{COLOR_NAME[opp]}方获胜！", "win")

    # ---------------------------------------------------------- 回合切换
    def end_turn(self):
        self.step_count += 1
        self.current_turn = se.opponent(self.current_turn)
        self.turn_phase = "roll"
        self.dice_value = None
        self.drawn_card = None
        self.frozen_zones = [z for z in self.frozen_zones if z["expire_step"] > self.step_count]
        self.ban_zones = [z for z in self.ban_zones if z["expire_step"] > self.step_count]
        self.bonus_uses = {"B": {}, "W": {}}  # 未使用的抽卡当回合作废

    # ---------------------------------------------------------- 序列化
    def to_dict(self) -> dict:
        return {
            "board": self.board,
            "current_turn": self.current_turn,
            "step_count": self.step_count,
            "warnings": self.warnings,
            "skills_remaining": {"B": self.skills_remaining("B"), "W": self.skills_remaining("W")},
            "frozen_zones": self.frozen_zones,
            "ban_zones": self.ban_zones,
            "peace_rounds": self.peace_rounds(),
            "last_move": self.last_move,
            "winner": self.winner,
            "win_reason": self.win_reason,
            "dice_value": self.dice_value,
            "turn_phase": self.turn_phase,
            "drawn_card": self.drawn_card,
            "immune": {c: self.is_immune(c) for c in ("B", "W")},
            "silenced": {c: self.is_silenced(c) for c in ("B", "W")},
        }


class Player:
    def __init__(self, player_id: str, name: str, color: str):
        self.id = player_id
        self.name = name
        self.color = color
        self.connected = True
        self.disconnected_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {"name": self.name, "color": self.color, "connected": self.connected}


class Room:
    def __init__(self, mode: str = "pvp"):
        self.id = uuid.uuid4().hex[:6].upper()
        self.mode = mode
        self.game = GameState()
        self.players: Dict[str, Player] = {}
        self.created_at = time.time()
        self.last_active = time.time()

    def touch(self):
        self.last_active = time.time()

    def add_player(self, name: str) -> Player:
        color = "B" if not any(p.color == "B" for p in self.players.values()) else "W"
        p = Player(uuid.uuid4().hex[:8], (name or "玩家")[:12], color)
        self.players[p.id] = p
        return p

    def is_full(self) -> bool:
        return len(self.players) >= 2

    def players_info(self) -> List[dict]:
        return [p.to_dict() for p in self.players.values()]


ROOMS: Dict[str, Room] = {}


def create_room(mode: str = "pvp") -> Room:
    room = Room(mode)
    if mode == "ai":
        room.players["AI_BOT"] = Player("AI_BOT", "AI 棋灵", "W")
    ROOMS[room.id] = room
    return room


def get_room(room_id: str) -> Optional[Room]:
    return ROOMS.get((room_id or "").upper())


def cleanup_rooms():
    """销毁 30 分钟无操作的房间；联机房全员断线 5 分钟后销毁"""
    now = time.time()
    doomed = []
    for rid, room in ROOMS.items():
        if now - room.last_active > 1800:
            doomed.append(rid)
            continue
        if room.mode == "pvp" and room.players and all(
            (not p.connected) and p.disconnected_at and now - p.disconnected_at > 300
            for p in room.players.values()
        ):
            doomed.append(rid)
    for rid in doomed:
        ROOMS.pop(rid, None)