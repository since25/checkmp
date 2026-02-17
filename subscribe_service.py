"""
订阅服务 - 业务逻辑层
组合 MPClient 提供高层业务功能
"""
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from mp_client import MPClient

# 语言代码映射（方便用中文查询）
LANGUAGE_MAP = {
    "韩语": "ko", "韩": "ko", "korean": "ko", "ko": "ko",
    "日语": "ja", "日": "ja", "japanese": "ja", "ja": "ja",
    "中文": "zh", "中": "zh", "chinese": "zh", "zh": "zh",
    "英语": "en", "英": "en", "english": "en", "en": "en",
    "法语": "fr", "法": "fr", "french": "fr", "fr": "fr",
    "西班牙语": "es", "spanish": "es", "es": "es",
    "泰语": "th", "泰": "th", "thai": "th", "th": "th",
}


class SubscribeService:
    """订阅服务"""

    def __init__(self, client: MPClient = None):
        self.client = client or MPClient()

    # ==================== 语言查询辅助 ====================

    def _get_language_for_item(self, item: dict) -> str:
        """查询单个条目的 original_language（通过 TMDB 详情）"""
        tmdb_id = item.get("tmdb_id")
        media_type = item.get("type", "电视剧")
        if not tmdb_id:
            return ""
        try:
            detail = self.client.get_media_detail(
                f"tmdb:{tmdb_id}", type_name=media_type
            )
            return detail.get("original_language", "") if detail else ""
        except Exception:
            return ""

    def _enrich_and_filter_by_lang(self, items: list, lang: str,
                                    target_count: int) -> list:
        """批量查询语言并过滤

        Args:
            items: 原始列表
            lang: 语言代码 (ko/ja/zh/en...) 或中文名
            target_count: 目标返回数量
        """
        # 解析语言代码
        lang_code = LANGUAGE_MAP.get(lang.lower(), lang.lower())

        results = []

        # 并发查询 TMDB 详情获取语言
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {
                executor.submit(self._get_language_for_item, item): item
                for item in items
            }
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    item_lang = future.result()
                    item["_original_language"] = item_lang
                    if item_lang == lang_code:
                        results.append(item)
                        if len(results) >= target_count:
                            # 取消剩余任务
                            for f in future_to_item:
                                f.cancel()
                            break
                except Exception:
                    pass

        return results

    # ==================== 热播内容 ====================

    def get_hot_tv(self, page: int = 1, count: int = 20,
                   genre_id: int = None, min_rating: float = None,
                   lang: str = None) -> list:
        """获取热播电视剧

        Args:
            lang: 可选，语言过滤。支持代码(ko/ja/zh/en)或中文(韩语/日语)
        """
        kwargs = {}
        if genre_id is not None:
            kwargs["genre_id"] = genre_id
        if min_rating is not None:
            kwargs["min_rating"] = min_rating

        if lang:
            # 开启语言过滤：拉取更多数据再过滤
            fetch_count = count * 5  # 多拉取以保证过滤后够用
            shows = self.client.get_popular_subscribes(
                stype="电视剧", page=page, count=fetch_count, **kwargs
            )
            filtered = self._enrich_and_filter_by_lang(shows, lang, count)
            return [self._format_media(item) for item in filtered]
        else:
            shows = self.client.get_popular_subscribes(
                stype="电视剧", page=page, count=count, **kwargs
            )
            return [self._format_media(item) for item in shows]

    def get_hot_movies(self, page: int = 1, count: int = 20,
                       genre_id: int = None, min_rating: float = None,
                       lang: str = None) -> list:
        """获取热播电影

        Args:
            lang: 可选，语言过滤。支持代码(ko/ja/zh/en)或中文(韩语/日语)
        """
        kwargs = {}
        if genre_id is not None:
            kwargs["genre_id"] = genre_id
        if min_rating is not None:
            kwargs["min_rating"] = min_rating

        if lang:
            fetch_count = count * 5
            movies = self.client.get_popular_subscribes(
                stype="电影", page=page, count=fetch_count, **kwargs
            )
            filtered = self._enrich_and_filter_by_lang(movies, lang, count)
            return [self._format_media(item) for item in filtered]
        else:
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
            "language": item.get("_original_language") or item.get("original_language", ""),
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
