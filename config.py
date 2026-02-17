"""
MoviePilot 配置管理模块
从 config_base.txt 读取配置，支持环境变量覆盖
"""
import os

# 默认配置
BASE_URL = ""
API_KEY = ""

# 本服务监听端口
SERVICE_PORT = 8899
SERVICE_HOST = "0.0.0.0"


def load_config(config_file: str = "config_base.txt"):
    """从配置文件加载配置"""
    global BASE_URL, API_KEY

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == "base_url":
                        BASE_URL = value.rstrip("/")
                    elif key == "api_key":
                        API_KEY = value

    # 环境变量覆盖
    BASE_URL = os.environ.get("MP_BASE_URL", BASE_URL)
    API_KEY = os.environ.get("MP_API_KEY", API_KEY)
    SERVICE_PORT_ENV = os.environ.get("SERVICE_PORT")
    if SERVICE_PORT_ENV:
        globals()["SERVICE_PORT"] = int(SERVICE_PORT_ENV)

    if not BASE_URL or not API_KEY:
        raise ValueError("请配置 base_url 和 api_key（config_base.txt 或环境变量）")


# 启动时自动加载
load_config()
