"""
测试代码生成器

将解析后的 TestCase 列表渲染为 pytest + httpx 测试代码文件。
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.models.test_case import TestCase

logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates"


def _operator_symbol(op: str) -> str:
    """将操作符字符串映射为 Python 运算符"""
    mapping = {
        "eq": "==",
        "ne": "!=",
        "gt": ">",
        "lt": "<",
        "ge": ">=",
        "le": "<=",
    }
    return mapping.get(op, "==")


def _pydantic_tojson(value, indent=None):
    """自定义 tojson 过滤器，支持 Pydantic BaseModel 序列化"""
    import json
    from pydantic import BaseModel

    def _convert(obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if isinstance(obj, list):
            return [_convert(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        return obj

    converted = _convert(value)
    return json.dumps(converted, ensure_ascii=False, indent=indent)


class TestGenerator:
    """测试代码生成器"""

    def __init__(
        self,
        output_dir: str | Path = "output",
        template_name: str = "test_template.py.j2",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_name = template_name

        # 初始化 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        # 注册自定义过滤器
        self.env.filters["operator_symbol"] = _operator_symbol
        self.env.filters["tojson"] = _pydantic_tojson

    def _group_by_module(self, cases: list[TestCase]) -> dict[str, list[TestCase]]:
        """按模块分组用例"""
        groups: dict[str, list[TestCase]] = defaultdict(list)
        for case in cases:
            groups[case.module].append(case)
        return dict(groups)

    def _make_filename(self, module: str) -> str:
        """生成测试文件名"""
        safe_name = module.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
        return f"test_{safe_name}.py"

    def generate(self, cases: list[TestCase]) -> list[Path]:
        """
        生成测试代码文件

        Args:
            cases: TestCase 列表

        Returns:
            生成的文件路径列表
        """
        if not cases:
            logger.warning("没有用例需要生成")
            return []

        template = self.env.get_template(self.template_name)
        grouped = self._group_by_module(cases)
        generated_files: list[Path] = []

        for module, module_cases in grouped.items():
            # 生成类名和文件名
            class_name = module_cases[0].class_name
            filename = self._make_filename(module)
            file_path = self.output_dir / filename

            # 检查是否有异步和数据驱动用例
            has_async = any(c.is_async for c in module_cases)
            has_data_driven = any(c.is_data_driven for c in module_cases)

            # 为模板准备上下文
            context = {
                "module": module,
                "class_name": class_name,
                "cases": module_cases,
                "gen_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "has_async": has_async,
                "has_data_driven": has_data_driven,
            }

            # 渲染模板
            try:
                rendered = template.render(**context)
                # 后处理：移除多余空行
                lines = rendered.split("\n")
                cleaned_lines = []
                prev_blank = False
                for line in lines:
                    is_blank = line.strip() == ""
                    if is_blank and prev_blank:
                        continue
                    cleaned_lines.append(line)
                    prev_blank = is_blank

                rendered = "\n".join(cleaned_lines)

                file_path.write_text(rendered, encoding="utf-8")
                generated_files.append(file_path)
                logger.info(
                    f"生成文件: {file_path} ({len(module_cases)} 条用例)"
                )
            except Exception as e:
                logger.error(f"生成文件 {filename} 失败: {e}")
                raise

        return generated_files

    def generate_conftest(self, env_config_path: str | Path = None) -> Path:
        """
        生成 conftest.py 文件

        Args:
            env_config_path: 环境配置文件路径

        Returns:
            conftest.py 路径
        """
        if env_config_path is None:
            env_config_path = PROJECT_ROOT / "config" / "env_config.yaml"

        conftest_content = '''"""
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
'''

        conftest_path = self.output_dir / "conftest.py"
        conftest_path.write_text(conftest_content, encoding="utf-8")
        logger.info(f"生成 conftest.py: {conftest_path}")
        return conftest_path
