"""
MoviePilot API 客户端封装
所有 API 调用通过 ?token=API_KEY 认证
"""
import requests
import urllib3
from typing import Optional, Union, List, Dict, Any
import config

# 禁用 SSL 警告（自签证书场景）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 请求超时时间（秒）
TIMEOUT = 15


class MPClient:
    """MoviePilot API 客户端"""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = (base_url or config.BASE_URL).rstrip("/")
        self.api_key = api_key or config.API_KEY

    def _request(self, method: str, path: str, params: dict = None,
                 json_data: dict = None) -> Optional[Union[dict, list]]:
        """发送请求，自动附加 token"""
        url = f"{self.base_url}{path}"
        params = params or {}
        params["token"] = self.api_key

        try:
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                verify=False,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise Exception(f"请求超时: {path}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP 错误 {resp.status_code}: {resp.text}")
        except Exception as e:
            raise Exception(f"请求失败: {e}")

    def _get(self, path: str, params: dict = None):
        return self._request("GET", path, params=params)

    def _post(self, path: str, params: dict = None, json_data: dict = None):
        return self._request("POST", path, params=params, json_data=json_data)

    def _put(self, path: str, params: dict = None, json_data: dict = None):
        return self._request("PUT", path, params=params, json_data=json_data)

    def _delete(self, path: str, params: dict = None, json_data: dict = None):
        return self._request("DELETE", path, params=params, json_data=json_data)

    # ==================== 订阅相关 ====================

    def get_subscribes(self) -> list:
        """获取所有订阅列表"""
        return self._get("/api/v1/subscribe/list") or []

    def add_subscribe(self, subscribe_data: dict) -> dict:
        """新增订阅
        subscribe_data 示例:
        {
            "name": "鱿鱼游戏",
            "type": "电视剧",
            "tmdbid": 93405,
            "year": "2021",
            "season": 2
        }
        """
        return self._post("/api/v1/subscribe/", json_data=subscribe_data)

    def delete_subscribe(self, subscribe_id: int) -> dict:
        """删除订阅"""
        return self._delete(f"/api/v1/subscribe/{subscribe_id}")

    def delete_subscribe_by_mediaid(self, mediaid: str, season: int = None) -> dict:
        """通过媒体ID删除订阅（格式: tmdb:12345 或 douban:12345）"""
        params = {}
        if season is not None:
            params["season"] = season
        return self._delete(f"/api/v1/subscribe/media/{mediaid}", params=params)

    def get_subscribe_by_mediaid(self, mediaid: str, season: int = None,
                                 title: str = None) -> Optional[dict]:
        """通过媒体ID查询订阅"""
        params = {}
        if season is not None:
            params["season"] = season
        if title:
            params["title"] = title
        return self._get(f"/api/v1/subscribe/media/{mediaid}", params=params)

    def get_popular_subscribes(self, stype: str = "电视剧", page: int = 1,
                                count: int = 20, **kwargs) -> list:
        """获取热门订阅
        stype: 电视剧 / 电影
        """
        params = {"stype": stype, "page": page, "count": count}
        params.update(kwargs)
        return self._get("/api/v1/subscribe/popular", params=params) or []

    # ==================== 媒体相关 ====================

    def search_media(self, title: str, media_type: str = "media",
                     page: int = 1, count: int = 8) -> list:
        """搜索媒体/人物信息"""
        return self._get("/api/v1/media/search", params={
            "title": title, "type": media_type, "page": page, "count": count
        }) or []

    def get_media_detail(self, mediaid: str, type_name: str,
                         title: str = None, year: str = None) -> dict:
        """获取媒体详情
        mediaid: tmdb:12345 或 douban:12345
        type_name: 电影 / 电视剧
        """
        params = {"type_name": type_name}
        if title:
            params["title"] = title
        if year:
            params["year"] = year
        return self._get(f"/api/v1/media/{mediaid}", params=params)

    def recognize_media(self, title: str, subtitle: str = None) -> dict:
        """识别媒体信息（根据标题）"""
        params = {"title": title}
        if subtitle:
            params["subtitle"] = subtitle
        return self._get("/api/v1/media/recognize2", params=params)

    # ==================== TMDB 相关 ====================

    def get_tmdb_seasons(self, tmdbid: int) -> list:
        """获取 TMDB 所有季信息"""
        return self._get(f"/api/v1/tmdb/seasons/{tmdbid}") or []

    def get_tmdb_recommend(self, tmdbid: int, type_name: str) -> list:
        """获取 TMDB 推荐内容"""
        return self._get(f"/api/v1/tmdb/recommend/{tmdbid}/{type_name}") or []

    def get_tmdb_similar(self, tmdbid: int, type_name: str) -> list:
        """获取类似内容"""
        return self._get(f"/api/v1/tmdb/similar/{tmdbid}/{type_name}") or []

    # ==================== Dashboard ====================

    def get_statistic(self) -> dict:
        """获取媒体数量统计"""
        return self._get("/api/v1/dashboard/statistic2")

    def get_storage(self) -> dict:
        """获取存储空间信息"""
        return self._get("/api/v1/dashboard/storage2")

    def get_downloader_info(self) -> dict:
        """获取下载器信息"""
        return self._get("/api/v1/dashboard/downloader2")

    def get_schedule(self) -> list:
        """获取后台服务状态"""
        return self._get("/api/v1/dashboard/schedule2") or []

    # ==================== 下载历史 ====================

    def get_download_history(self, page: int = 1, count: int = 30) -> list:
        """获取下载历史"""
        return self._get("/api/v1/history/download", params={
            "page": page, "count": count
        }) or []

    # ==================== 系统 ====================

    def get_system_env(self) -> dict:
        """获取系统配置信息"""
        return self._get("/api/v1/system/env")
