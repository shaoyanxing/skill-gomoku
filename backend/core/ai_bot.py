"""单机 AI：启发式评分落子 + 概率性技能释放"""
import copy
import random
from typing import List, Optional, Tuple

from models.schemas import SkillName
from core import skills as se

SCORE_FIVE = 10000
SCORE_OPEN_FOUR = 5000
SCORE_FOUR = 500       # 冲四
SCORE_OPEN_THREE = 100  # 活三
SCORE_THREE = 30
SCORE_TWO = 10


def _line_score(board, x, y, dx, dy, color) -> int:
    count = 1
    open_ends = 0
    nx, ny = x + dx, y + dy
    while se.in_board(nx, ny) and board[ny][nx] == color:
        count += 1
        nx += dx
        ny += dy
    if se.in_board(nx, ny) and board[ny][nx] == "":
        open_ends += 1
    nx, ny = x - dx, y - dy
    while se.in_board(nx, ny) and board[ny][nx] == color:
        count += 1
        nx -= dx
        ny -= dy
    if se.in_board(nx, ny) and board[ny][nx] == "":
        open_ends += 1
    if count >= 5:
        return SCORE_FIVE
    if count == 4:
        return SCORE_OPEN_FOUR if open_ends == 2 else (SCORE_FOUR if open_ends == 1 else 0)
    if count == 3:
        return SCORE_OPEN_THREE if open_ends == 2 else (SCORE_THREE if open_ends == 1 else 0)
    if count == 2:
        return SCORE_TWO if open_ends else 0
    return 1 if open_ends == 2 else 0


def _point_score(board, x, y, color) -> int:
    return sum(_line_score(board, x, y, dx, dy, color) for dx, dy in se.DIRECTIONS)


def _near_stones(board, x, y, dist=2) -> bool:
    for yy in range(max(0, y - dist), min(se.BOARD_SIZE, y + dist + 1)):
        for xx in range(max(0, x - dist), min(se.BOARD_SIZE, x + dist + 1)):
            if board[yy][xx]:
                return True
    return False


def best_move(board, color) -> Optional[Tuple[int, int]]:
    opp = se.opponent(color)
    empties = [(x, y) for y in range(se.BOARD_SIZE) for x in range(se.BOARD_SIZE) if not board[y][x]]
    if not empties:
        return None
    if len(empties) == se.BOARD_SIZE * se.BOARD_SIZE:
        return (7, 7)
    best, best_score = None, -1.0
    for x, y in empties:
        if not _near_stones(board, x, y):
            continue
        board[y][x] = color
        attack = _point_score(board, x, y, color)
        board[y][x] = opp
        defense = _point_score(board, x, y, opp)
        board[y][x] = ""
        score = attack + defense * 0.9 + random.random() * 5
        if score > best_score:
            best_score, best = score, (x, y)
    return best or random.choice(empties)


def _attempt_skill(game, color, skill: SkillName) -> bool:
    """为 AI 构造参数并预校验，尽量避免犯规；成功返回 True"""
    opp = se.opponent(color)
    tx = ty = None
    extra = {}
    if skill == SkillName.FEI_SHA_ZOU_SHI:
        if game.is_immune(opp):
            return False
        target = None
        if game.last_move and game.board[game.last_move[1]][game.last_move[0]] == opp:
            target = tuple(game.last_move)
        else:
            opp_stones = [(x, y) for y in range(15) for x in range(15) if game.board[y][x] == opp]
            if opp_stones:
                target = min(opp_stones, key=lambda s: abs(s[0] - 7) + abs(s[1] - 7))
        if not target:
            return False
        tx, ty = target
    elif skill == SkillName.BO_YUN_JIAN_RI:
        movable = [
            y for y in range(15)
            if any(
                game.board[y][x] == color
                and ((x + 1 < 15 and not game.board[y][x + 1]) or (x - 1 >= 0 and not game.board[y][x - 1]))
                for x in range(15)
            )
        ]
        if not movable:
            return False
        ty = random.choice(movable)
        tx = 0
    elif skill == SkillName.BING_DONG_SAN_CHI:
        tx, ty = (game.last_move if game.last_move else (7, 7))
    elif skill == SkillName.AN_DU_CHEN_CANG:
        found = False
        for cy in range(1, 14):
            for cx in range(1, 14):
                if game.board[cy][cx]:
                    continue
                total = sum(
                    1 for yy in range(cy - 1, cy + 2) for xx in range(cx - 1, cx + 2)
                    if game.board[yy][xx]
                )
                if total <= 4:
                    found = True
                    break
            if found:
                break
        if not found:
            return False
    elif skill == SkillName.YI_HUA_JIE_MU:
        my_count = sum(row.count(color) for row in game.board)
        if my_count < 2 or not se.find_live_threes(game.board, opp):
            return False
    elif skill == SkillName.ZONG_HENG_TIAN_XIA:
        mine = [(x, y) for y in range(15) for x in range(15) if game.board[y][x] == color]
        empt = [
            (x, y) for y in range(15) for x in range(15)
            if not game.board[y][x] and not game.is_frozen(x, y) and not game.is_banned(x, y)
        ]
        if not mine or not empt:
            return False
        fx, fy = random.choice(mine)
        tx, ty = min(empt, key=lambda p: min(abs(p[0] - mx) + abs(p[1] - my) for mx, my in mine))
        extra = {"from_x": fx, "from_y": fy}
    elif skill in (SkillName.PAI_SHAN_DAO_HAI, SkillName.LI_BA_SHAN_XI):
        # 位移技能：模拟执行，自己的连子数无增益则放弃
        clone = copy.deepcopy(game)
        before = se.max_chain(game.board, color)
        res = se.DISPATCH[skill](clone, color)
        if not res.get("ok") or se.max_chain(clone.board, color) <= before:
            return False
    result = game.apply_skill(color, skill.value, tx, ty, extra)
    return bool(result.get("ok"))


def _try_skill(game, color) -> bool:
    order: List[SkillName] = []
    # 0. 抽到的卡优先使用
    if game.drawn_card:
        order.append(SkillName(game.drawn_card))
    # 1. 飞沙走石干扰玩家
    order.append(SkillName.FEI_SHA_ZOU_SHI)
    # 2. 棋子过少时优先铺场
    my_count = sum(row.count(color) for row in game.board)
    if my_count < 4:
        order += [SkillName.AN_DU_CHEN_CANG, SkillName.BO_YUN_JIAN_RI]
    # 3. 位移技能（需验证增益）
    order += [SkillName.PAI_SHAN_DAO_HAI, SkillName.LI_BA_SHAN_XI]
    # 4. 其余兜底
    order += [
        SkillName.BING_DONG_SAN_CHI, SkillName.JING_RU_ZHI_SHUI, SkillName.BU_DONG_RU_SHAN,
        SkillName.ZONG_HENG_TIAN_XIA, SkillName.YI_HUA_JIE_MU, SkillName.AN_DU_CHEN_CANG,
        SkillName.BO_YUN_JIAN_RI,
    ]
    seen = set()
    for skill in order:
        if skill in seen:
            continue
        seen.add(skill)
        if game.remaining(color, skill) <= 0:
            continue
        if _attempt_skill(game, color, skill):
            return True
    return False


def ai_act(game, color: str = "W"):
    """AI 执行一回合动作（直接修改 game）。调用前应已完成掷骰"""
    if game.turn_phase == "roll":
        game.roll_dice()
    phase = game.turn_phase
    use_skill = False
    if phase == "skill":
        use_skill = True
    elif phase == "move_or_skill":
        # 有抽到的卡必用，否则 20% 概率主动放技能
        use_skill = bool(game.drawn_card) or random.random() < 0.2
    if use_skill and _try_skill(game, color):
        return
    if phase == "skill":
        # 强制技能回合兜底：逐个尝试所有技能
        for skill in se.SKILL_LIMITS:
            if game.remaining(color, skill) > 0 and _attempt_skill(game, color, skill):
                return
    mv = best_move(game.board, color)
    if mv:
        game.apply_move(color, mv[0], mv[1])