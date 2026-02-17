"""
TMDB 原生 API 客户端
使用 Read Access Token 直接调用 TMDB Discover/Search 接口
"""
import requests
from typing import Optional, List
import config


class TMDBClient:
    """TMDB API 客户端"""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p"

    def __init__(self, token: str = None):
        self.token = token or config.TMDB_TOKEN
        if not self.token:
            raise ValueError("请配置 tmdb_read_access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        """发送 GET 请求"""
        url = f"{self.BASE_URL}{path}"
        resp = requests.get(url, params=params, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ==================== Discover (发现) ====================

    def discover_tv(self, lang: str = "ko", sort_by: str = "popularity.desc",
                    page: int = 1, min_vote_count: int = 5,
                    min_vote_average: float = None,
                    first_air_date_gte: str = None,
                    first_air_date_lte: str = None,
                    with_genres: str = None) -> dict:
        """发现电视剧

        Args:
            lang: 原始语言代码 (ko/ja/zh/en...)
            sort_by: 排序方式 (popularity.desc / first_air_date.desc / vote_average.desc)
            page: 页码
            min_vote_count: 最低投票数（过滤冷门内容）
            min_vote_average: 最低评分
            first_air_date_gte: 首播日期 >= (YYYY-MM-DD)
            first_air_date_lte: 首播日期 <= (YYYY-MM-DD)
            with_genres: 类型 ID (逗号分隔)

        Returns:
            {"page": 1, "total_pages": 519, "total_results": 10363, "results": [...]}
        """
        params = {
            "with_original_language": lang,
            "sort_by": sort_by,
            "page": page,
            "language": "zh-CN",
            "vote_count.gte": min_vote_count,
        }
        if min_vote_average:
            params["vote_average.gte"] = min_vote_average
        if first_air_date_gte:
            params["first_air_date.gte"] = first_air_date_gte
        if first_air_date_lte:
            params["first_air_date.lte"] = first_air_date_lte
        if with_genres:
            params["with_genres"] = with_genres

        data = self._get("/discover/tv", params=params)
        return {
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "total_results": data.get("total_results", 0),
            "results": [self._format_tv(item) for item in data.get("results", [])],
        }

    def discover_movie(self, lang: str = "ko", sort_by: str = "popularity.desc",
                       page: int = 1, min_vote_count: int = 5,
                       min_vote_average: float = None,
                       release_date_gte: str = None,
                       release_date_lte: str = None,
                       with_genres: str = None) -> dict:
        """发现电影

        Args:
            lang: 原始语言代码
            sort_by: 排序方式
            release_date_gte: 上映日期 >= (YYYY-MM-DD)
            release_date_lte: 上映日期 <= (YYYY-MM-DD)
        """
        params = {
            "with_original_language": lang,
            "sort_by": sort_by,
            "page": page,
            "language": "zh-CN",
            "vote_count.gte": min_vote_count,
        }
        if min_vote_average:
            params["vote_average.gte"] = min_vote_average
        if release_date_gte:
            params["primary_release_date.gte"] = release_date_gte
        if release_date_lte:
            params["primary_release_date.lte"] = release_date_lte
        if with_genres:
            params["with_genres"] = with_genres

        data = self._get("/discover/movie", params=params)
        return {
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "total_results": data.get("total_results", 0),
            "results": [self._format_movie(item) for item in data.get("results", [])],
        }

    # ==================== Trending (趋势) ====================

    def trending_tv(self, time_window: str = "week") -> list:
        """获取趋势电视剧 (全语言)

        Args:
            time_window: day / week
        """
        data = self._get(f"/trending/tv/{time_window}", params={"language": "zh-CN"})
        return [self._format_tv(item) for item in data.get("results", [])]

    def trending_movie(self, time_window: str = "week") -> list:
        """获取趋势电影 (全语言)"""
        data = self._get(f"/trending/movie/{time_window}", params={"language": "zh-CN"})
        return [self._format_movie(item) for item in data.get("results", [])]

    # ==================== Detail (详情) ====================

    def tv_detail(self, tmdb_id: int) -> dict:
        """获取电视剧详情"""
        data = self._get(f"/tv/{tmdb_id}", params={"language": "zh-CN"})
        result = self._format_tv(data)
        result["seasons"] = [
            {
                "season_number": s.get("season_number"),
                "name": s.get("name"),
                "episode_count": s.get("episode_count"),
                "air_date": s.get("air_date"),
            }
            for s in data.get("seasons", [])
            if s.get("season_number", 0) > 0  # 排除特别篇(S0)
        ]
        result["number_of_seasons"] = data.get("number_of_seasons")
        result["status"] = data.get("status")
        result["genres"] = [g.get("name") for g in data.get("genres", [])]
        return result

    def movie_detail(self, tmdb_id: int) -> dict:
        """获取电影详情"""
        data = self._get(f"/movie/{tmdb_id}", params={"language": "zh-CN"})
        result = self._format_movie(data)
        result["runtime"] = data.get("runtime")
        result["status"] = data.get("status")
        result["genres"] = [g.get("name") for g in data.get("genres", [])]
        return result

    # ==================== 格式化 ====================

    def _format_tv(self, item: dict) -> dict:
        """格式化电视剧信息"""
        poster = item.get("poster_path", "")
        backdrop = item.get("backdrop_path", "")
        return {
            "tmdb_id": item.get("id"),
            "title": item.get("name", ""),
            "original_title": item.get("original_name", ""),
            "type": "电视剧",
            "language": item.get("original_language", ""),
            "first_air_date": item.get("first_air_date", ""),
            "rating": round(item.get("vote_average", 0), 1),
            "popularity": round(item.get("popularity", 0), 1),
            "overview": item.get("overview", ""),
            "poster": f"{self.IMAGE_BASE}/w500{poster}" if poster else "",
            "backdrop": f"{self.IMAGE_BASE}/w500{backdrop}" if backdrop else "",
        }

    def _format_movie(self, item: dict) -> dict:
        """格式化电影信息"""
        poster = item.get("poster_path", "")
        backdrop = item.get("backdrop_path", "")
        return {
            "tmdb_id": item.get("id"),
            "title": item.get("title", ""),
            "original_title": item.get("original_title", ""),
            "type": "电影",
            "language": item.get("original_language", ""),
            "release_date": item.get("release_date", ""),
            "rating": round(item.get("vote_average", 0), 1),
            "popularity": round(item.get("popularity", 0), 1),
            "overview": item.get("overview", ""),
            "poster": f"{self.IMAGE_BASE}/w500{poster}" if poster else "",
            "backdrop": f"{self.IMAGE_BASE}/w500{backdrop}" if backdrop else "",
        }
