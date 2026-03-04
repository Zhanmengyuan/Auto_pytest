"""
自动生成的 conftest.py
提供 httpx 客户端 fixture 和环境配置
"""

import pytest
import httpx
import yaml
from pathlib import Path


def _load_env_config():
    """加载环境配置"""
    config_path = Path(__file__).parent.parent / "config" / "env_config.yaml"
    if not config_path.exists():
        return {
            "base_url": "http://localhost:8080",
            "timeout": 30,
            "headers": {"Content-Type": "application/json"},
        }
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    active = config.get("active_env", "dev")
    env_settings = config.get("environments", {}).get(active, {})
    return env_settings


def _build_headers(env_config: dict) -> dict:
    """构建请求头（含认证信息）"""
    headers = dict(env_config.get("headers", {}))
    auth = env_config.get("auth", {})
    auth_type = auth.get("type", "none")

    if auth_type == "bearer":
        headers["Authorization"] = f"Bearer {auth.get('token', '')}"
    elif auth_type == "api_key":
        headers[auth.get("header_name", "X-API-Key")] = auth.get("key", "")

    return headers


@pytest.fixture(scope="session")
def env_config():
    """环境配置 fixture"""
    return _load_env_config()


@pytest.fixture(scope="session")
async def async_client(env_config):
    """异步 httpx 客户端 fixture"""
    base_url = env_config.get("base_url", "http://localhost:8080")
    timeout = env_config.get("timeout", 30)
    headers = _build_headers(env_config)

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def sync_client(env_config):
    """同步 httpx 客户端 fixture"""
    base_url = env_config.get("base_url", "http://localhost:8080")
    timeout = env_config.get("timeout", 30)
    headers = _build_headers(env_config)

    with httpx.Client(
        base_url=base_url,
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
    ) as client:
        yield client


def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        choices=["dev", "test", "prod"],
        help="选择运行环境: dev / test / prod",
    )


@pytest.fixture(scope="session", autouse=True)
def set_env(request):
    """根据命令行参数设置环境"""
    env = request.config.getoption("--env")
    config_path = Path(__file__).parent.parent / "config" / "env_config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["active_env"] = env
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)
