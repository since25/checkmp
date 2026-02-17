# CheckMP - MoviePilot 订阅服务

一个轻量级 API 服务，封装 [MoviePilot](https://github.com/jxxghp/MoviePilot) API，提供热播剧推荐、订阅管理、媒体搜索等功能。

专为 **OpenClaw 机器人** 设计，可通过 HTTP 接口方便调用。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config_base.txt`（已在 `.gitignore` 中，不会被提交）：

```
base_url = "https://your-moviepilot-host:port"
api_key = "your_api_key"
```

或通过环境变量：

```bash
export MP_BASE_URL="https://your-moviepilot-host:port"
export MP_API_KEY="your_api_key"
```

### 3. 启动服务

```bash
python main.py
```

服务启动后访问 `http://localhost:8899/docs` 查看 Swagger API 文档。

## 📡 API 接口

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/hot/tv` | GET | 热播电视剧列表 |
| `/api/hot/movie` | GET | 热播电影列表 |
| `/api/subscribe` | GET | 当前订阅列表 |
| `/api/subscribe` | POST | 新增订阅 |
| `/api/subscribe/{id}` | DELETE | 删除订阅 |
| `/api/subscribe/check` | GET | 检查订阅状态 |
| `/api/search` | GET | 搜索媒体 |
| `/api/stats` | GET | 系统统计摘要 |
| `/api/health` | GET | 健康检查 |

### 使用示例

```bash
# 热播电视剧
curl http://localhost:8899/api/hot/tv

# 热播电影（评分 > 7）
curl "http://localhost:8899/api/hot/movie?min_rating=7"

# 搜索
curl "http://localhost:8899/api/search?title=鱿鱼游戏"

# 通过标题订阅
curl -X POST http://localhost:8899/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"title": "鱿鱼游戏", "type": "电视剧", "season": 2}'

# 通过 TMDB ID 订阅
curl -X POST http://localhost:8899/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"tmdb_id": 93405, "type": "电视剧"}'

# 当前订阅
curl http://localhost:8899/api/subscribe

# 统计信息
curl http://localhost:8899/api/stats
```

## 📁 项目结构

```
checkmp/
├── config.py              # 配置管理
├── config_base.txt        # 配置文件（不提交 Git）
├── mp_client.py           # MoviePilot API 客户端
├── subscribe_service.py   # 订阅服务逻辑
├── main.py                # FastAPI 入口
├── requirements.txt       # 依赖
└── README.md
```

## 🔗 参考

- [MoviePilot API 文档](https://api.movie-pilot.org/)
- [MoviePilot 项目](https://github.com/jxxghp/MoviePilot)