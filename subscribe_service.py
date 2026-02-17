"""
订阅服务 - 业务逻辑层
组合 MPClient 提供高层业务功能
"""
from typing import Optional
from mp_client import MPClient


class SubscribeService:
    """订阅服务"""

    def __init__(self, client: MPClient = None):
        self.client = client or MPClient()

    # ==================== 热播内容 ====================

    def get_hot_tv(self, page: int = 1, count: int = 20,
                   genre_id: int = None, min_rating: float = None) -> list:
        """获取热播电视剧"""
        kwargs = {}
        if genre_id is not None:
            kwargs["genre_id"] = genre_id
        if min_rating is not None:
            kwargs["min_rating"] = min_rating
        shows = self.client.get_popular_subscribes(
            stype="电视剧", page=page, count=count, **kwargs
        )
        return [self._format_media(item) for item in shows]

    def get_hot_movies(self, page: int = 1, count: int = 20,
                       genre_id: int = None, min_rating: float = None) -> list:
        """获取热播电影"""
        kwargs = {}
        if genre_id is not None:
            kwargs["genre_id"] = genre_id
        if min_rating is not None:
            kwargs["min_rating"] = min_rating
        movies = self.client.get_popular_subscribes(
            stype="电影", page=page, count=count, **kwargs
        )
        return [self._format_media(item) for item in movies]

    # ==================== 订阅管理 ====================

    def list_subscribes(self) -> list:
        """获取当前所有订阅"""
        subs = self.client.get_subscribes()
        return [self._format_subscribe(s) for s in subs]

    def subscribe_by_tmdbid(self, tmdbid: int, media_type: str = "电视剧",
                             season: int = None) -> dict:
        """通过 TMDB ID 订阅

        Args:
            tmdbid: TMDB ID
            media_type: "电影" 或 "电视剧"
            season: 季号（仅电视剧）
        """
        # 先搜索获取媒体信息
        results = self.client.search_media(str(tmdbid))
        media_info = None
        for r in results:
            if r.get("tmdb_id") == tmdbid:
                media_info = r
                break

        sub_data = {
            "tmdbid": tmdbid,
            "type": media_type,
        }

        if media_info:
            sub_data["name"] = media_info.get("title", "")
            sub_data["year"] = media_info.get("year", "")
            sub_data["poster"] = media_info.get("poster_path", "")
            sub_data["backdrop"] = media_info.get("backdrop_path", "")
            sub_data["vote"] = media_info.get("vote_average", 0)
            sub_data["description"] = media_info.get("overview", "")

        if season is not None and media_type == "电视剧":
            sub_data["season"] = season

        return self.client.add_subscribe(sub_data)

    def subscribe_by_title(self, title: str, media_type: str = None,
                            season: int = None) -> dict:
        """通过标题搜索并订阅第一个匹配结果

        Args:
            title: 媒体标题
            media_type: 可选，"电影" 或 "电视剧"，不指定则使用搜索结果的类型
            season: 季号（仅电视剧）
        """
        results = self.client.search_media(title)
        if not results:
            return {"success": False, "message": f"未找到: {title}"}

        media = results[0]
        tmdbid = media.get("tmdb_id")
        if not tmdbid:
            return {"success": False, "message": f"无法获取 TMDB ID: {title}"}

        mtype = media_type or media.get("type", "电视剧")
        return self.subscribe_by_tmdbid(tmdbid, media_type=mtype, season=season)

    def unsubscribe(self, subscribe_id: int) -> dict:
        """取消订阅"""
        return self.client.delete_subscribe(subscribe_id)

    def check_subscribe(self, tmdbid: int, season: int = None) -> Optional[dict]:
        """检查是否已订阅"""
        mediaid = f"tmdb:{tmdbid}"
        try:
            return self.client.get_subscribe_by_mediaid(mediaid, season=season)
        except Exception:
            return None

    # ==================== 搜索 ====================

    def search(self, title: str, page: int = 1, count: int = 8) -> list:
        """搜索媒体"""
        results = self.client.search_media(title, page=page, count=count)
        return [self._format_media(item) for item in results]

    # ==================== 统计 ====================

    def get_stats(self) -> dict:
        """获取系统统计摘要"""
        stat = self.client.get_statistic() or {}
        storage = None
        downloader = None
        try:
            storage = self.client.get_storage()
        except Exception:
            pass
        try:
            downloader = self.client.get_downloader_info()
        except Exception:
            pass

        return {
            "media": {
                "movie_count": stat.get("movie_count", 0),
                "tv_count": stat.get("tv_count", 0),
                "episode_count": stat.get("episode_count", 0),
                "user_count": stat.get("user_count", 0),
            },
            "storage": storage,
            "downloader": downloader,
        }

    # ==================== 格式化 ====================

    @staticmethod
    def _format_media(item: dict) -> dict:
        """格式化媒体信息为简洁格式"""
        return {
            "title": item.get("title", ""),
            "year": item.get("year", ""),
            "type": item.get("type", ""),
            "tmdb_id": item.get("tmdb_id"),
            "douban_id": item.get("douban_id"),
            "rating": item.get("vote_average", 0),
            "overview": item.get("overview", ""),
            "poster": item.get("poster_path", ""),
            "backdrop": item.get("backdrop_path", ""),
            "season": item.get("season"),
        }

    @staticmethod
    def _format_subscribe(item: dict) -> dict:
        """格式化订阅信息"""
        return {
            "id": item.get("id"),
            "name": item.get("name", ""),
            "year": item.get("year", ""),
            "type": item.get("type", ""),
            "tmdb_id": item.get("tmdbid"),
            "season": item.get("season"),
            "poster": item.get("poster", ""),
            "rating": item.get("vote", 0),
            "description": item.get("description", ""),
            "state": item.get("state", ""),
        }
