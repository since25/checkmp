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

app = FastAPI(
    title="CheckMP - MoviePilot 订阅服务",
    description="MoviePilot API 封装，提供热播剧推荐、订阅管理、媒体搜索等功能",
    version="1.0.0",
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


# ==================== 请求模型 ====================

class SubscribeRequest(BaseModel):
    """订阅请求"""
    tmdb_id: Optional[int] = None
    title: Optional[str] = None
    type: Optional[str] = "电视剧"  # 电影 / 电视剧
    season: Optional[int] = None


# ==================== 热播内容 ====================

@app.get("/api/hot/tv", summary="热播电视剧", tags=["热播推荐"])
def hot_tv(
    page: int = Query(1, description="页码"),
    count: int = Query(20, description="每页数量"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    lang: Optional[str] = Query(None, description="语言过滤: ko(韩语)/ja(日语)/zh(中文)/en(英语)，也支持中文如'韩语'"),
):
    """获取热播电视剧列表（支持语言过滤）"""
    try:
        return service.get_hot_tv(page=page, count=count, min_rating=min_rating, lang=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hot/movie", summary="热播电影", tags=["热播推荐"])
def hot_movie(
    page: int = Query(1, description="页码"),
    count: int = Query(20, description="每页数量"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    lang: Optional[str] = Query(None, description="语言过滤: ko(韩语)/ja(日语)/zh(中文)/en(英语)，也支持中文如'韩语'"),
):
    """获取热播电影列表（支持语言过滤）"""
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
    - 通过 tmdb_id 直接订阅
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
    return {"status": "ok", "service": "checkmp"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        reload=True,
    )
