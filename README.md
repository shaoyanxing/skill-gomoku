# 🀄 技能五子棋 Skill-Gomoku

五子棋打腻了？来试试带技能的。

这不是普通的五子棋。每回合你得先扔个骰子——单数落子、双数抽技能卡。11 种武侠技能能让棋盘上整排棋子平移、冻住对手的区域、把对方的活三偷过来变成你的，甚至全场禁用技能两回合。每 5 步还有强制技能回合，三次犯规直接判负。

在线试玩：[blog.shaoyanxing.top/gomoku](https://blog.shaoyanxing.top/gomoku/)

---

## 快速开始

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 前端（另一个终端）
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173` 即可。前端连的后端地址在 `frontend/.env.development` 里配（默认 `localhost:8000`）。

### Docker 一键启动

```bash
docker compose up -d
```

---

## 玩法

### 基础规则

1. **掷骰🎲**：每回合先扔一个 3D 骰子
   - **单数** → 本回合落子
   - **双数** → 抽一张技能卡，当回合可以用一次（不用就作废）
2. **落子♟️**：15×15 棋盘，五子连珠获胜
3. **技能🃏**：分三类，共 11 种（详见下方）
4. **强制技能⚡**：每 5 步强制释放一个技能（不消耗回合）
5. **犯规⚠️**：技能放错了记犯规，累计 3 次直接判负

### 技能一览

#### 🔶 位移系 — 动棋盘上的子

| 技能 | 图标 | 次数 | 效果 |
|------|------|------|------|
| 排山倒海 | 🌊 | 3 | 全体棋子向随机方向平移 1 格，边界阻挡则不动 |
| 飞沙走石 | 🌪️ | 3 | 移除目标点的对方棋子，该点本回合禁落 |
| 移花接木 | 🎭 | **1** | 夺取对方活三中的一子，己方随机 2 子倒戈 |
| 力拔山兮 | ⛰️ | 3 | 全体棋子向随机方向位移 1~2 格，越界的被震落 |
| 拨云见日 | 🌤️ | 3 | 选中一整行，己方棋子整体左/右移 1 格 |

#### 🔷 凝结系 — 限制对手

| 技能 | 图标 | 次数 | 效果 |
|------|------|------|------|
| 静如止水 | 💧 | 2 | 封印对手下回合的技能 |
| 冰冻三尺 | ❄️ | 3 | 冻结目标周围 3×3 区域，禁止落子 3 回合 |
| 不动如山 | 🛡️ | 2 | 本回合棋子免疫位移，对手强用凝结技反噬 |

#### 🔷 阴阳系 — 扭转战局

| 技能 | 图标 | 次数 | 效果 |
|------|------|------|------|
| 无为而治 | ☯️ | **1** | 双方 2 回合内禁用所有技能 |
| 暗渡陈仓 | 🥷 | 3 | 在棋子稀疏的区域中心自动落一子 |
| 纵横天下 | 👑 | 2 | 传送己方 1 子至任意空位，封印对手下回合技能 |

### 联机

一人创建联机房间，把 6 位房间号发给好友，对方输入号码加入即可对战。断线后 5 分钟内可重连恢复对局，房间 30 分钟无操作自动销毁。

---

## 架构

```
技能五子棋
├── backend/          FastAPI + WebSocket
│   ├── main.py              入口：CORS、路由、房间清理后台任务
│   ├── core/
│   │   ├── game_state.py    游戏状态 & 房间管理（内存）
│   │   ├── skills.py        11 种技能效果引擎
│   │   └── ai_bot.py        启发式 AI 棋灵
│   ├── routers/
│   │   ├── game.py          房间 CRUD (REST)
│   │   └── websocket.py     游戏操作 (WebSocket)
│   └── models/
│       └── schemas.py       数据模型
│
└── frontend/         Vue 3 + Vite + Canvas
    ├── src/
    │   ├── stores/
    │   │   └── gameStore.js  全局状态（Pinia）
    │   ├── components/
    │   │   ├── GameBoard.vue  Canvas 棋盘
    │   │   ├── RoomManager.vue 大厅
    │   │   ├── SkillPanel.vue  技能面板
    │   │   ├── Dice3D.vue     3D CSS 骰子
    │   │   ├── CardDraw.vue   抽卡动画
    │   │   └── StatusBar.vue  状态栏
    │   ├── utils/
    │   │   ├── websocket.js   WebSocket 封装（心跳+重连）
    │   │   └── skills.js      技能元数据
    │   └── composables/
    │       └── useBoardLogic.js 棋盘逻辑
    └── package.json
```

### 数据流

```
浏览器 ←→ WebSocket ←→ FastAPI 后端 ←→ 内存房间/GameState
   ↑                                      ↑
   Pinia Store                    AI 棋灵 (ai_bot.py)
   Canvas 渲染                    技能引擎 (skills.py)
```

- **WebSocket** 是全双工通信主力：掷骰、落子、放技能、事件推送、状态同步都在一条长连接上完成
- **REST** 只负责开局：创建房间、加入房间两个端点
- **服务端是权威**：所有逻辑判定在 `GameState` 中执行，前端仅做展示和用户交互

### 设计要点

- **GameState** 是纯逻辑对象，不依赖网络层，可独立测试。`test_core.py` 验证核心规则
- **技能引擎** 用 `DISPATCH` 字典做函数分发，新增技能只需写一个 `skill_xxx()` 函数 + 在 `SKILL_LIMITS` 注册次数
- **AI** 是启发式评分 + 概率技能选择，纯规则驱动，没有机器学习。`best_move` 对每个空位评估攻击分 + 防守分，`_try_skill` 按优先级依次尝试
- **GameSocket** 类封装了指数退避重连（最多 8 次，最长 15 秒间隔）+ 30 秒心跳，生产环境断线恢复可靠

### 技术栈

| 层 | 技术 |
|---|------|
| 前端框架 | Vue 3 (Composition API) + Vite |
| 状态管理 | Pinia |
| 棋盘渲染 | Canvas 2D |
| 3D 骰子 | 纯 CSS 3D 立方体 + `preserve-3d` |
| 通信 | WebSocket + Axios (REST) |
| 后端框架 | FastAPI + Uvicorn |
| 游戏逻辑 | Python 纯内存对象 |
| AI | 启发式评分 |

---

## 项目背景

这个项目的原版来自另一位开发者，我 fork 之后对照它的架构重构了自己的版本。详情见对应的博客文章。

## License

MIT
