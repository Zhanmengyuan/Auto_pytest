"""
YAML 用例解析器

从 YAML 文件中读取功能用例，转换为 TestCase 模型列表。

YAML 用例格式直接使用结构化数据，比 Excel 更直观，天然支持
嵌套的断言、前置步骤、数据驱动等复杂结构，无需 JSON 字符串。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from src.models.test_case import TestCase

logger = logging.getLogger(__name__)


class YamlParser:
    """YAML 用例解析器"""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        if self.file_path.suffix not in (".yaml", ".yml"):
            raise ValueError(
                f"不支持的文件格式: {self.file_path.suffix}，请使用 .yaml 或 .yml"
            )

    def parse(self) -> list[TestCase]:
        """
        解析 YAML 文件，返回 TestCase 列表

        Returns:
            TestCase 模型列表
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if raw is None:
            logger.warning("YAML 文件为空")
            return []

        # 支持两种顶层结构:
        #   1. 直接是列表: [{case_id: ..., ...}, ...]
        #   2. 带 cases 键: {cases: [{...}, ...], global_config: {...}}
        if isinstance(raw, list):
            cases_data = raw
            global_config: dict[str, Any] = {}
        elif isinstance(raw, dict):
            cases_data = raw.get("cases", [])
            global_config = raw.get("global_config", {})
        else:
            logger.error(f"YAML 格式不正确，期望列表或字典，得到: {type(raw)}")
            return []

        if not cases_data:
            logger.warning("YAML 文件中没有用例数据")
            return []

        test_cases: list[TestCase] = []

        for idx, case_dict in enumerate(cases_data, start=1):
            if not isinstance(case_dict, dict):
                logger.warning(f"第 {idx} 条用例格式不正确，跳过")
                continue

            # 合并全局配置（用例级别可覆盖全局）
            merged = {**global_config, **case_dict}

            case_id = merged.get("case_id", "")
            if not case_id:
                logger.warning(f"第 {idx} 条用例无 case_id，跳过")
                continue

            try:
                tc = TestCase(**merged)
                test_cases.append(tc)
                logger.info(f"解析成功: 第 {idx} 条 -> {tc.case_id}: {tc.title}")
            except Exception as e:
                logger.error(f"解析失败: 第 {idx} 条 (case_id={case_id}) -> {e}")

        logger.info(f"共解析 {len(test_cases)} 条用例 (来源: {self.file_path.name})")
        return test_cases


def parse_dir(dir_path: str | Path) -> list[TestCase]:
    """
    解析目录下所有 YAML 用例文件

    Args:
        dir_path: 存放 YAML 文件的目录

    Returns:
        所有文件合并后的 TestCase 列表
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"目录不存在: {path}")

    all_cases: list[TestCase] = []
    yaml_files = sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml"))

    if not yaml_files:
        logger.warning(f"目录 {path} 下未找到 YAML 文件")
        return []

    for f in yaml_files:
        logger.info(f"正在解析: {f.name}")
        parser = YamlParser(f)
        cases = parser.parse()
        all_cases.extend(cases)

    logger.info(f"目录 {path} 下共解析 {len(all_cases)} 条用例 ({len(yaml_files)} 个文件)")
    return all_cases


def parse_file(file_path: str | Path) -> list[TestCase]:
    """
    解析单个 YAML 用例文件

    Args:
        file_path: YAML 文件路径

    Returns:
        TestCase 模型列表
    """
    parser = YamlParser(file_path)
    return parser.parse()
