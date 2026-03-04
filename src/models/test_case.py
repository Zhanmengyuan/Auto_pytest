"""
测试用例数据模型

定义功能用例的结构化数据模型，用于在解析器和生成器之间传递数据。
"""

from __future__ import annotations

import json
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class SetupStep(BaseModel):
    """前置操作步骤"""
    description: str = Field(default="", description="步骤描述")
    method: str = Field(default="GET", description="HTTP 方法")
    url: str = Field(default="", description="请求路径")
    headers: dict[str, str] = Field(default_factory=dict, description="请求头")
    body: dict[str, Any] = Field(default_factory=dict, description="请求体")
    extract: dict[str, str] = Field(
        default_factory=dict,
        description="从响应中提取变量，格式: {变量名: jsonpath表达式}",
    )


class Assertion(BaseModel):
    """断言项"""
    type: str = Field(
        default="status_code",
        description="断言类型: status_code / json_field / header / contains / schema",
    )
    field: str = Field(default="", description="要断言的字段路径 (jsonpath)")
    operator: str = Field(
        default="eq",
        description="比较操作: eq / ne / gt / lt / ge / le / in / not_in / contains / regex",
    )
    expected: Any = Field(default=None, description="期望值")


class TestData(BaseModel):
    """数据驱动的单组测试数据"""
    name: str = Field(default="", description="数据组名称/描述")
    params: dict[str, Any] = Field(default_factory=dict, description="查询参数")
    body: dict[str, Any] = Field(default_factory=dict, description="请求体")
    headers: dict[str, str] = Field(default_factory=dict, description="额外请求头")
    assertions: list[Assertion] = Field(default_factory=list, description="该组数据的断言")


class TestCase(BaseModel):
    """
    功能用例模型 —— 一个完整的接口测试用例描述

    对应 Excel 中的一行或一组行数据。
    """

    # ---- 基础信息 ----
    case_id: str = Field(description="用例编号，如 TC_001")
    module: str = Field(default="default", description="所属模块")
    title: str = Field(description="用例标题")
    description: str = Field(default="", description="用例描述")
    priority: str = Field(default="P1", description="优先级: P0/P1/P2/P3")
    tags: list[str] = Field(default_factory=list, description="标签列表")

    # ---- 接口信息 ----
    method: str = Field(description="HTTP 方法: GET/POST/PUT/DELETE/PATCH")
    path: str = Field(description="接口路径，如 /api/v1/users")
    headers: dict[str, str] = Field(default_factory=dict, description="自定义请求头")
    params: dict[str, Any] = Field(default_factory=dict, description="Query 参数")
    body: dict[str, Any] = Field(default_factory=dict, description="请求体 (JSON)")
    content_type: str = Field(default="application/json", description="请求内容类型")

    # ---- 前置条件 ----
    setup_steps: list[SetupStep] = Field(
        default_factory=list, description="前置操作步骤列表"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="依赖的用例编号列表"
    )

    # ---- 断言 ----
    expected_status: int = Field(default=200, description="预期 HTTP 状态码")
    assertions: list[Assertion] = Field(default_factory=list, description="断言列表")

    # ---- 数据驱动 ----
    test_data: list[TestData] = Field(
        default_factory=list, description="数据驱动测试数据组"
    )

    # ---- 元信息 ----
    is_async: bool = Field(default=True, description="是否使用异步请求")
    skip: bool = Field(default=False, description="是否跳过")
    skip_reason: str = Field(default="", description="跳过原因")

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in ("P0", "P1", "P2", "P3"):
            return "P1"
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        if isinstance(v, list):
            return v
        return []

    @field_validator("headers", "params", "body", mode="before")
    @classmethod
    def parse_json_field(cls, v: Any) -> dict:
        if isinstance(v, str):
            if not v.strip():
                return {}
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        if isinstance(v, dict):
            return v
        return {}

    @field_validator("assertions", mode="before")
    @classmethod
    def parse_assertions(cls, v: Any) -> list[Assertion]:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [Assertion(**item) if isinstance(item, dict) else item for item in data]
                elif isinstance(data, dict):
                    return [Assertion(**data)]
            except json.JSONDecodeError:
                return []
        return v if v else []

    @field_validator("setup_steps", mode="before")
    @classmethod
    def parse_setup_steps(cls, v: Any) -> list[SetupStep]:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [SetupStep(**item) if isinstance(item, dict) else item for item in data]
                elif isinstance(data, dict):
                    return [SetupStep(**data)]
            except json.JSONDecodeError:
                return []
        return v if v else []

    @field_validator("test_data", mode="before")
    @classmethod
    def parse_test_data(cls, v: Any) -> list[TestData]:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [TestData(**item) if isinstance(item, dict) else item for item in data]
                elif isinstance(data, dict):
                    return [TestData(**data)]
            except json.JSONDecodeError:
                return []
        return v if v else []

    @field_validator("depends_on", mode="before")
    @classmethod
    def parse_depends_on(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [d.strip() for d in v.split(",") if d.strip()]
        return v if v else []

    @property
    def is_data_driven(self) -> bool:
        """是否为数据驱动用例"""
        return len(self.test_data) > 0

    @property
    def function_name(self) -> str:
        """生成测试函数名"""
        safe_id = self.case_id.lower().replace("-", "_").replace(".", "_")
        return f"test_{safe_id}"

    @property
    def class_name(self) -> str:
        """生成测试类名"""
        parts = self.module.replace("-", "_").replace(".", "_").split("_")
        return "Test" + "".join(p.capitalize() for p in parts if p)
