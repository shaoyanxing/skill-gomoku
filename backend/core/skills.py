"""技能效果引擎：技能判定、犯规检查与棋盘修改。

所有技能函数约定：
    fn(game, color, tx=None, ty=None, extra=None) -> dict
返回 dict 至少包含：
    ok:   bool  技能是否生效
    foul: bool  是否构成犯规（调用方负责记警告）
    msg:  str   展示给玩家的文案
"""
import random
import re
from typing import Dict, List, Optional, Tuple

from models.schemas import SkillName

BOARD_SIZE = 15
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
DIRS8 = DIRECTIONS + [(-1, 0), (0, -1), (-1, -1), (-1, 1)]
DIR_NAMES = {
    (1, 0): "右", (-1, 0): "左", (0, 1): "下", (0, -1): "上",
    (1, 1): "右下", (-1, -1): "左上", (1, -1): "右上", (-1, 1): "左下",
}

# 每个技能的可用次数（全局）
SKILL_LIMITS: Dict[SkillName, int] = {
    SkillName.PAI_SHAN_DAO_HAI: 3,
    SkillName.FEI_SHA_ZOU_SHI: 3,
    SkillName.YI_HUA_JIE_MU: 1,
    SkillName.LI_BA_SHAN_XI: 3,
    SkillName.BO_YUN_JIAN_RI: 3,
    SkillName.JING_RU_ZHI_SHUI: 2,
    SkillName.BING_DONG_SAN_CHI: 3,
    SkillName.BU_DONG_RU_SHAN: 2,
    SkillName.WU_WEI_ER_ZHI: 1,
    SkillName.AN_DU_CHEN_CANG: 3,
    SkillName.ZONG_HENG_TIAN_XIA: 2,
}

# 技能分类：move=位移 freeze=凝结 yinyang=阴阳
SKILL_CATEGORY: Dict[SkillName, str] = {
    SkillName.PAI_SHAN_DAO_HAI: "move",
    SkillName.FEI_SHA_ZOU_SHI: "move",
    SkillName.YI_HUA_JIE_MU: "move",
    SkillName.LI_BA_SHAN_XI: "move",
    SkillName.BO_YUN_JIAN_RI: "move",
    SkillName.JING_RU_ZHI_SHUI: "freeze",
    SkillName.BING_DONG_SAN_CHI: "freeze",
    SkillName.BU_DONG_RU_SHAN: "freeze",
    SkillName.WU_WEI_ER_ZHI: "yinyang",
    SkillName.AN_DU_CHEN_CANG: "yinyang",
    SkillName.ZONG_HENG_TIAN_XIA: "yinyang",
}


def opponent(color: str) -> str:
    return "W" if color == "B" else "B"


def in_board(x: int, y: int) -> bool:
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE


def check_five(board, x: int, y: int, color: str) -> bool:
    for dx, dy in DIRECTIONS:
        count = 1
        for sign in (1, -1):
            nx, ny = x + dx * sign, y + dy * sign
            while in_board(nx, ny) and board[ny][nx] == color:
                count += 1
                nx += dx * sign
                ny += dy * sign
        if count >= 5:
            return True
    return False


def has_five(board, color: str) -> bool:
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] == color and check_five(board, x, y, color):
                return True
    return False


def max_chain(board, color: str) -> int:
    best = 0
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] != color:
                continue
            for dx, dy in DIRECTIONS:
                count = 1
                nx, ny = x + dx, y + dy
                while in_board(nx, ny) and board[ny][nx] == color:
                    count += 1
                    nx += dx
                    ny += dy
                best = max(best, count)
    return best


def _all_lines() -> List[List[Tuple[int, int]]]:
    lines = []
    for y in range(BOARD_SIZE):
        lines.append([(x, y) for x in range(BOARD_SIZE)])
    for x in range(BOARD_SIZE):
        lines.append([(x, y) for y in range(BOARD_SIZE)])
    for sx in range(BOARD_SIZE):
        lines.append([(sx + i, i) for i in range(BOARD_SIZE - sx)])
    for sy in range(1, BOARD_SIZE):
        lines.append([(i, sy + i) for i in range(BOARD_SIZE - sy)])
    for sx in range(BOARD_SIZE):
        lines.append([(sx + i, BOARD_SIZE - 1 - i) for i in range(sx + 1)])
    for sy in range(BOARD_SIZE - 1):
        lines.append([(i, sy - i) for i in range(sy + 1)])
    return [ln for ln in lines if len(ln) >= 5]


_LINES = _all_lines()
_LIVE_THREE = re.compile(r"(?=(\.XXX\.|\.XX\.X\.|\.X\.XX\.))")


def find_live_threes(board, color: str) -> List[Tuple[int, int]]:
    """返回参与活三（含跳活三）的棋子坐标列表"""
    opp = opponent(color)
    found = set()
    for line in _LINES:
        s = "".join(
            "X" if board[y][x] == color else ("O" if board[y][x] == opp else ".")
            for (x, y) in line
        )
        padded = "O" + s + "O"
        for m in _LIVE_THREE.finditer(padded):
            for k in range(6):
                li = m.start() + k - 1
                if 0 <= li < len(line) and s[li] == "X":
                    found.add(line[li])
    return sorted(found)


def _stones(board, color: Optional[str] = None) -> List[Tuple[int, int]]:
    return [
        (x, y)
        for y in range(BOARD_SIZE)
        for x in range(BOARD_SIZE)
        if board[y][x] and (color is None or board[y][x] == color)
    ]


# ---------------------------------------------------------------- 位移类

def skill_pai_shan_dao_hai(game, color, tx=None, ty=None, extra=None):
    """排山倒海：全体棋子向随机方向平移1格，边界阻挡则不动"""
    dx, dy = random.choice(DIRS8)
    board = game.board
    stones = _stones(board)
    stones.sort(key=lambda s: s[0] * dx + s[1] * dy, reverse=True)
    moved = []
    for x, y in stones:
        c = board[y][x]
        if not c or game.is_immune(c):
            continue
        nx, ny = x + dx, y + dy
        if in_board(nx, ny) and board[ny][nx] == "":
            board[ny][nx] = c
            board[y][x] = ""
            moved.append({"from": [x, y], "to": [nx, ny], "color": c})
    if not moved:
        return {"ok": False, "foul": True, "msg": "排山倒海未能移动任何棋子，记犯规一次！"}
    return {
        "ok": True,
        "msg": f"排山倒海！全体棋子向{DIR_NAMES[(dx, dy)]}平移，共移动 {len(moved)} 子",
        "anim": "shift", "moved_stones": moved,
    }


def skill_fei_sha_zou_shi(game, color, tx, ty, extra=None):
    """飞沙走石：移除目标点对方棋子，该点本回合禁落"""
    opp = opponent(color)
    if tx is None or ty is None or not in_board(tx, ty):
        return {"ok": False, "foul": False, "msg": "飞沙走石需要指定目标！"}
    if game.board[ty][tx] != opp:
        return {"ok": False, "foul": True, "msg": "目标位置没有对方棋子，记犯规一次！"}
    if game.is_immune(opp):
        return {"ok": False, "foul": False, "msg": "对方不动如山生效，飞沙走石被拦截！"}
    game.board[ty][tx] = ""
    game.ban_zones.append({"x": tx, "y": ty, "expire_step": game.step_count + 2})
    return {
        "ok": True,
        "msg": f"飞沙走石！卷走了 ({tx},{ty}) 的敌子，该点位本回合禁落",
        "anim": "remove", "removed": [{"at": [tx, ty], "color": opp}],
    }


def skill_yi_hua_jie_mu(game, color, tx=None, ty=None, extra=None):
    """移花接木：夺取对方活三中一子，己方随机2子倒戈（全局1次）"""
    opp = opponent(color)
    threes = find_live_threes(game.board, opp)
    mine = _stones(game.board, color)
    if not threes or len(mine) < 2:
        return {"ok": False, "foul": True, "msg": "对方不存在活三，或己方棋子不足2枚，记犯规一次！"}
    sx, sy = random.choice(threes)
    game.board[sy][sx] = color
    for (x, y) in random.sample(mine, 2):
        game.board[y][x] = opp
    return {
        "ok": True,
        "msg": f"移花接木！夺取敌子 ({sx},{sy})，代价是己方 2 子倒戈",
        "anim": "swap",
    }


def skill_li_ba_shan_xi(game, color, tx=None, ty=None, extra=None):
    """力拔山兮：全体棋子向随机方向位移1~2格，越界者被震落"""
    dx, dy = random.choice(DIRS8)
    dist = random.randint(1, 2)
    board = game.board
    stones = _stones(board)
    stones.sort(key=lambda s: s[0] * dx + s[1] * dy, reverse=True)
    moved, removed = [], []
    for x, y in stones:
        c = board[y][x]
        if not c or game.is_immune(c):
            continue
        nx, ny = x + dx * dist, y + dy * dist
        if not in_board(nx, ny):
            board[y][x] = ""
            removed.append({"at": [x, y], "color": c})
        elif board[ny][nx] == "":
            board[ny][nx] = c
            board[y][x] = ""
            moved.append({"from": [x, y], "to": [nx, ny], "color": c})
    if not moved and not removed:
        return {"ok": False, "foul": True, "msg": "力拔山兮未能撼动任何棋子，记犯规一次！"}
    msg = f"力拔山兮！向{DIR_NAMES[(dx, dy)]}位移 {dist} 格：移动 {len(moved)} 子"
    if removed:
        msg += f"，震落 {len(removed)} 子"
    return {"ok": True, "msg": msg, "anim": "shift", "moved_stones": moved, "removed": removed}


def skill_bo_yun_jian_ri(game, color, tx=None, ty=None, extra=None):
    """拨云见日：选择一行，己方棋子整体左/右移1格（遇阻不动）"""
    if ty is None or not (0 <= ty < BOARD_SIZE):
        return {"ok": False, "foul": False, "msg": "拨云见日需要点击目标行！"}
    dx = random.choice([1, -1])
    board = game.board
    row_stones = [x for x in range(BOARD_SIZE) if board[ty][x] == color]
    if not row_stones:
        return {"ok": False, "foul": True, "msg": "该行没有己方棋子，记犯规一次！"}
    row_stones.sort(key=lambda x: x * dx, reverse=True)
    moved = []
    for x in row_stones:
        nx = x + dx
        if in_board(nx, ty) and board[ty][nx] == "":
            board[ty][nx] = color
            board[ty][x] = ""
            moved.append({"from": [x, ty], "to": [nx, ty], "color": color})
    if not moved:
        return {"ok": False, "foul": True, "msg": "拨云见日被阻挡，未移动任何棋子，记犯规一次！"}
    return {
        "ok": True,
        "msg": f"拨云见日！第 {ty + 1} 行己方棋子向{DIR_NAMES[(dx, 0)]}移动 {len(moved)} 子",
        "anim": "shift", "moved_stones": moved,
    }


# ---------------------------------------------------------------- 凝结类

def skill_jing_ru_zhi_shui(game, color, tx=None, ty=None, extra=None):
    """静如止水：封印对手下回合的技能"""
    opp = opponent(color)
    game.skill_ban[opp] = max(game.skill_ban.get(opp, 0), game.step_count + 2)
    return {"ok": True, "msg": "静如止水！对手下回合无法使用技能", "anim": "silence"}


def skill_bing_dong_san_chi(game, color, tx, ty, extra=None):
    """冰冻三尺：冻结目标周围 3x3 区域 3 回合"""
    if tx is None or ty is None or not in_board(tx, ty):
        return {"ok": False, "foul": False, "msg": "冰冻三尺需要指定目标！"}
    game.frozen_zones.append({"x": tx, "y": ty, "expire_step": game.step_count + 6})
    return {
        "ok": True,
        "msg": f"冰冻三尺！({tx},{ty}) 周围 3x3 区域冻结 3 回合，禁止落子",
        "anim": "freeze",
    }


def skill_bu_dong_ru_shan(game, color, tx=None, ty=None, extra=None):
    """不动如山：本回合己方棋子免疫位移，并反制对手凝结技"""
    game.immune[color] = max(game.immune.get(color, 0), game.step_count + 2)
    return {
        "ok": True,
        "msg": "不动如山！你的棋子本回合免疫位移，对手强行使用凝结技将被反噬",
        "anim": "shield",
    }


# ---------------------------------------------------------------- 阴阳类

def skill_wu_wei_er_zhi(game, color, tx=None, ty=None, extra=None):
    """无为而治：双方 2 回合内禁用所有技能（全局1次）"""
    game.peace_until_step = game.step_count + 4
    return {"ok": True, "msg": "无为而治！双方 2 回合内无法使用任何技能", "anim": "peace"}


def skill_an_du_chen_cang(game, color, tx=None, ty=None, extra=None):
    """暗渡陈仓：在棋子稀疏（3x3 内 ≤4 子）且中心为空的位置自动落子"""
    candidates = []
    for cy in range(1, BOARD_SIZE - 1):
        for cx in range(1, BOARD_SIZE - 1):
            if game.board[cy][cx]:
                continue
            total = sum(
                1
                for yy in range(cy - 1, cy + 2)
                for xx in range(cx - 1, cx + 2)
                if game.board[yy][xx]
            )
            if total <= 4:
                candidates.append((cx, cy))
    if not candidates:
        return {"ok": False, "foul": True, "msg": "棋盘上找不到合适的暗渡点，记犯规一次！"}
    cx, cy = random.choice(candidates)
    game.board[cy][cx] = color
    game.last_move = [cx, cy]
    return {"ok": True, "msg": f"暗渡陈仓！奇兵落子 ({cx},{cy})", "anim": "drop"}


def skill_zong_heng_tian_xia(game, color, tx, ty, extra=None):
    """纵横天下：传送己方1子至空位，并封印对手下回合技能（全局2次）"""
    opp = opponent(color)
    fx = fy = None
    if extra:
        fx, fy = extra.get("from_x"), extra.get("from_y")
    if fx is None or fy is None or not in_board(fx, fy) or game.board[fy][fx] != color:
        return {"ok": False, "foul": False, "msg": "请先选择要传送的己方棋子！"}
    if tx is None or ty is None or not in_board(tx, ty):
        return {"ok": False, "foul": False, "msg": "请选择传送落点！"}
    if game.board[ty][tx] != "":
        return {"ok": False, "foul": True, "msg": "传送落点必须为空位，记犯规一次！"}
    if game.is_frozen(tx, ty) or game.is_banned(tx, ty):
        return {"ok": False, "foul": False, "msg": "目标点被冻结/封锁，无法传送！"}
    game.board[fy][fx] = ""
    game.board[ty][tx] = color
    game.skill_ban[opp] = max(game.skill_ban.get(opp, 0), game.step_count + 2)
    game.last_move = [tx, ty]
    return {
        "ok": True,
        "msg": f"纵横天下！棋子 ({fx},{fy}) 传送至 ({tx},{ty})，对手下回合技能被封印",
        "anim": "teleport",
    }


DISPATCH = {
    SkillName.PAI_SHAN_DAO_HAI: skill_pai_shan_dao_hai,
    SkillName.FEI_SHA_ZOU_SHI: skill_fei_sha_zou_shi,
    SkillName.YI_HUA_JIE_MU: skill_yi_hua_jie_mu,
    SkillName.LI_BA_SHAN_XI: skill_li_ba_shan_xi,
    SkillName.BO_YUN_JIAN_RI: skill_bo_yun_jian_ri,
    SkillName.JING_RU_ZHI_SHUI: skill_jing_ru_zhi_shui,
    SkillName.BING_DONG_SAN_CHI: skill_bing_dong_san_chi,
    SkillName.BU_DONG_RU_SHAN: skill_bu_dong_ru_shan,
    SkillName.WU_WEI_ER_ZHI: skill_wu_wei_er_zhi,
    SkillName.AN_DU_CHEN_CANG: skill_an_du_chen_cang,
    SkillName.ZONG_HENG_TIAN_XIA: skill_zong_heng_tian_xia,
}