# 🀄 技能五子棋 · Skill Gomoku

骰子驱动 + 抽卡技能的五子棋变体。单机可战 AI，联机可与友博弈。

## 玩法

每回合先**掷骰子**：
- **单数（1/3/5）** → 落子
- **双数（2/4/6）** → 抽一张技能卡，本回合可落子 + 用技能

技能不继承、每个技能有限使用次数，用完即止。

## 技术栈

```
Frontend:  Vue 3 + Vite + Pinia + Canvas
Backend:   Python FastAPI + Uvicorn + WebSocket
Deploy:    Cloudflare Tunnel → Nginx reverse proxy
```

## 快速开始

```bash
# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd frontend
npm install
npm run dev
```

生产部署时需设置环境变量：
```bash
cd frontend
VITE_API_BASE_URL=/gomoku VITE_WS_BASE_URL=/gomoku/ws npm run build
```

## 目录结构

```
skill-gomoku/
├── backend/
│   ├── main.py                # FastAPI 入口 + CORS
│   ├── core/
│   │   ├── game_state.py      # 游戏状态 + 房间管理
│   │   ├── skills.py          # 11个技能逻辑 + 棋盘工具
│   │   └── ai_bot.py          # 启发式 AI
│   ├── routers/
│   │   ├── game.py            # 房间 REST API
│   │   └── websocket.py       # WebSocket 实时对战
│   └── models/schemas.py      # Pydantic 模型
└── frontend/
    └── src/
        ├── stores/gameStore.js        # Pinia 状态机
        ├── components/
        │   ├── GameBoard.vue           # Canvas 棋盘
        │   ├── Dice3D.vue              # 3D CSS 骰子
        │   ├── CardDraw.vue            # 抽卡动画
        │   ├── SkillPanel.vue          # 技能面板
        │   ├── StatusBar.vue           # 状态栏
        │   └── RoomManager.vue         # 大厅/房间管理
        ├── composables/               # 可复用逻辑
        ├── utils/                     # 工具函数
        └── App.vue                    # 主组件
```

## License

MIT
