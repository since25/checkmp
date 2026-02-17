"""
CheckMP - MoviePilot 订阅服务 API
供 OpenClaw 机器人调用的 HTTP 接口
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

import config
from subscribe_service import SubscribeService
from tmdb_client import TMDBClient

app = FastAPI(
    title="CheckMP - MoviePilot 订阅服务",
    description="TMDB 发现 + MoviePilot 订阅，为 OpenClaw 机器人提供热播剧推荐与订阅管理",
    version="2.0.0",
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
service = SubscribeService()
tmdb = TMDBClient()


# ==================== 请求模型 ====================

class SubscribeRequest(BaseModel):
    """订阅请求"""
    tmdb_id: Optional[int] = None
    title: Optional[str] = None
    type: Optional[str] = "电视剧"  # 电影 / 电视剧
    season: Optional[int] = None


# ==================== TMDB 发现 (核心功能) ====================

@app.get("/api/tmdb/discover/tv", summary="TMDB 发现电视剧", tags=["TMDB 发现"])
def tmdb_discover_tv(
    lang: str = Query("ko", description="语言: ko(韩语)/ja(日语)/zh(中文)/en(英语)"),
    sort_by: str = Query("popularity.desc", description="排序: popularity.desc / first_air_date.desc / vote_average.desc"),
    page: int = Query(1, description="页码"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    date_from: Optional[str] = Query(None, description="首播日期起始 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="首播日期截止 (YYYY-MM-DD)"),
):
    """通过 TMDB 发现电视剧（按语言/时间/评分/热度筛选）"""
    try:
        return tmdb.discover_tv(
            lang=lang, sort_by=sort_by, page=page,
            min_vote_average=min_rating,
            first_air_date_gte=date_from,
            first_air_date_lte=date_to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/discover/movie", summary="TMDB 发现电影", tags=["TMDB 发现"])
def tmdb_discover_movie(
    lang: str = Query("ko", description="语言: ko(韩语)/ja(日语)/zh(中文)/en(英语)"),
    sort_by: str = Query("popularity.desc", description="排序: popularity.desc / primary_release_date.desc / vote_average.desc"),
    page: int = Query(1, description="页码"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    date_from: Optional[str] = Query(None, description="上映日期起始 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="上映日期截止 (YYYY-MM-DD)"),
):
    """通过 TMDB 发现电影（按语言/时间/评分/热度筛选）"""
    try:
        return tmdb.discover_movie(
            lang=lang, sort_by=sort_by, page=page,
            min_vote_average=min_rating,
            release_date_gte=date_from,
            release_date_lte=date_to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/trending/tv", summary="TMDB 趋势电视剧", tags=["TMDB 发现"])
def tmdb_trending_tv(
    time_window: str = Query("week", description="时间窗口: day / week"),
):
    """获取全球趋势电视剧"""
    try:
        return tmdb.trending_tv(time_window=time_window)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/trending/movie", summary="TMDB 趋势电影", tags=["TMDB 发现"])
def tmdb_trending_movie(
    time_window: str = Query("week", description="时间窗口: day / week"),
):
    """获取全球趋势电影"""
    try:
        return tmdb.trending_movie(time_window=time_window)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/tv/{tmdb_id}", summary="TMDB 电视剧详情", tags=["TMDB 发现"])
def tmdb_tv_detail(tmdb_id: int):
    """获取电视剧详情（含各季信息）"""
    try:
        return tmdb.tv_detail(tmdb_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/movie/{tmdb_id}", summary="TMDB 电影详情", tags=["TMDB 发现"])
def tmdb_movie_detail(tmdb_id: int):
    """获取电影详情"""
    try:
        return tmdb.movie_detail(tmdb_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MP 热播内容 ====================

@app.get("/api/hot/tv", summary="MP 热播电视剧", tags=["MP 热播推荐"])
def hot_tv(
    page: int = Query(1, description="页码"),
    count: int = Query(20, description="每页数量"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    lang: Optional[str] = Query(None, description="语言过滤: ko(韩语)/ja(日语)/zh(中文)/en(英语)"),
):
    """获取 MoviePilot 社区热播电视剧列表"""
    try:
        return service.get_hot_tv(page=page, count=count, min_rating=min_rating, lang=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hot/movie", summary="MP 热播电影", tags=["MP 热播推荐"])
def hot_movie(
    page: int = Query(1, description="页码"),
    count: int = Query(20, description="每页数量"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    lang: Optional[str] = Query(None, description="语言过滤: ko(韩语)/ja(日语)/zh(中文)/en(英语)"),
):
    """获取 MoviePilot 社区热播电影列表"""
    try:
        return service.get_hot_movies(page=page, count=count, min_rating=min_rating, lang=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 订阅管理 ====================

@app.get("/api/subscribe", summary="订阅列表", tags=["订阅管理"])
def list_subscribes():
    """获取当前所有订阅"""
    try:
        return service.list_subscribes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/subscribe", summary="新增订阅", tags=["订阅管理"])
def add_subscribe(req: SubscribeRequest):
    """新增订阅

    支持两种方式：
    - 通过 tmdb_id 直接订阅（推荐：从 TMDB 发现中选择后传入 tmdb_id）
    - 通过 title 搜索后订阅第一个匹配结果
    """
    try:
        if req.tmdb_id:
            return service.subscribe_by_tmdbid(
                tmdbid=req.tmdb_id,
                media_type=req.type,
                season=req.season,
            )
        elif req.title:
            return service.subscribe_by_title(
                title=req.title,
                media_type=req.type,
                season=req.season,
            )
        else:
            raise HTTPException(status_code=400, detail="请提供 tmdb_id 或 title")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/subscribe/{subscribe_id}", summary="删除订阅", tags=["订阅管理"])
def delete_subscribe(subscribe_id: int):
    """删除订阅"""
    try:
        return service.unsubscribe(subscribe_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subscribe/check", summary="检查订阅状态", tags=["订阅管理"])
def check_subscribe(
    tmdb_id: int = Query(..., description="TMDB ID"),
    season: Optional[int] = Query(None, description="季号"),
):
    """检查某个媒体是否已订阅"""
    result = service.check_subscribe(tmdbid=tmdb_id, season=season)
    if result:
        return {"subscribed": True, "detail": result}
    return {"subscribed": False}


# ==================== 搜索 ====================

@app.get("/api/search", summary="搜索媒体", tags=["搜索"])
def search_media(
    title: str = Query(..., description="搜索关键词"),
    page: int = Query(1, description="页码"),
    count: int = Query(8, description="每页数量"),
):
    """搜索媒体信息"""
    try:
        return service.search(title=title, page=page, count=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计 ====================

@app.get("/api/stats", summary="系统统计", tags=["统计"])
def get_stats():
    """获取系统统计摘要（媒体数量、存储空间、下载器）"""
    try:
        return service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@app.get("/api/health", summary="健康检查", tags=["系统"])
def health_check():
    """健康检查"""
    return {"status": "ok", "service": "checkmp", "version": "2.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        reload=True,
    )

