"""
自动生成的接口测试文件
模块: user
生成时间: 2026-03-04 11:05:16
"""

import json
import pytest
import httpx
import pytest_asyncio

# ============================================
# 数据驱动测试数据
# ============================================
test_tc_003_data = [
    {
        "name": "正常登录",
        "params": {},
        "body": {
            "username": "admin",
            "password": "123456"
        },
        "headers": {},
        "assertions": [
            {
                "type": "status_code",
                "field": "",
                "operator": "eq",
                "expected": 200
            },
            {
                "type": "json_field",
                "field": "data.token",
                "operator": "ne",
                "expected": ""
            }
        ]
    },
    {
        "name": "密码错误",
        "params": {},
        "body": {
            "username": "admin",
            "password": "wrong_password"
        },
        "headers": {},
        "assertions": [
            {
                "type": "status_code",
                "field": "",
                "operator": "eq",
                "expected": 200
            },
            {
                "type": "json_field",
                "field": "code",
                "operator": "eq",
                "expected": 401
            }
        ]
    },
    {
        "name": "用户名为空",
        "params": {},
        "body": {
            "username": "",
            "password": "123456"
        },
        "headers": {},
        "assertions": [
            {
                "type": "status_code",
                "field": "",
                "operator": "eq",
                "expected": 200
            },
            {
                "type": "json_field",
                "field": "code",
                "operator": "eq",
                "expected": 400
            }
        ]
    }
]

class TestUser:
    """user 模块接口测试"""

    # --------------------------------------------------
    # TC_001: 获取用户列表
    # --------------------------------------------------
    @pytest.mark.smoke
    @pytest.mark.user
    @pytest.mark.p0
    @pytest.mark.asyncio
    async def test_tc_001(self, async_client: httpx.AsyncClient):
        """
        获取用户列表
        验证获取用户列表接口正常返回
        优先级: P0
        """
        _params = {"page": 1, "size": 10}
        _body = {}
        _headers = {}

        # ---- 发送请求 ----
        response = await async_client.request(
            method="GET",
            url="/api/v1/users",
            params=_params if _params else None,
            headers=_headers if _headers else None,
        )

        # ---- 断言 ----
        assert response.status_code == 200, (
            f"状态码不匹配: 预期 200, 实际 {response.status_code}, "
            f"响应: {response.text[:500]}"
        )

        # 断言: JSON 字段 code eq 0
        _resp_json = response.json()
        _actual_val = _extract_json_path(_resp_json, "code")
        assert _actual_val == 0, (
            f"字段 'code' 不匹配: 预期 0, 实际 {_actual_val}"
        )

        # 断言: JSON 字段 data.total gt 0
        _resp_json = response.json()
        _actual_val = _extract_json_path(_resp_json, "data.total")
        assert _actual_val > 0

    # --------------------------------------------------
    # TC_002: 创建新用户
    # --------------------------------------------------
    @pytest.mark.user
    @pytest.mark.create
    @pytest.mark.p0
    @pytest.mark.asyncio
    async def test_tc_002(self, async_client: httpx.AsyncClient):
        """
        创建新用户
        验证创建用户接口
        优先级: P0
        """
        _params = {}
        _body = {"name": "张三", "email": "zhangsan@test.com", "age": 28}
        _headers = {}

        # ---- 发送请求 ----
        response = await async_client.request(
            method="POST",
            url="/api/v1/users",
            params=_params if _params else None,
            json=_body if _body else None,
            headers=_headers if _headers else None,
        )

        # ---- 断言 ----
        assert response.status_code == 201, (
            f"状态码不匹配: 预期 201, 实际 {response.status_code}, "
            f"响应: {response.text[:500]}"
        )

        # 断言: JSON 字段 code eq 0
        _resp_json = response.json()
        _actual_val = _extract_json_path(_resp_json, "code")
        assert _actual_val == 0, (
            f"字段 'code' 不匹配: 预期 0, 实际 {_actual_val}"
        )

        # 断言: JSON 字段 data.name eq 张三
        _resp_json = response.json()
        _actual_val = _extract_json_path(_resp_json, "data.name")
        assert _actual_val == "张三", (
            f"字段 'data.name' 不匹配: 预期 "张三", 实际 {_actual_val}"
        )

    # --------------------------------------------------
    # TC_003: 用户登录-多场景
    # --------------------------------------------------
    @pytest.mark.user
    @pytest.mark.login
    @pytest.mark.p0
    @pytest.mark.parametrize(
        "test_data_item",
        test_tc_003_data,
        ids=[d.get("name", f"data_{i}") for i, d in enumerate(test_tc_003_data)],
    )
    @pytest.mark.asyncio
    async def test_tc_003(self, async_client: httpx.AsyncClient, test_data_item: dict):
        """
        用户登录-多场景
        数据驱动验证登录接口的正常和异常场景
        优先级: P0
        """
        # ---- 数据驱动：合并参数 ----
        _params = {}
        _params.update(test_data_item.get("params", {}))
        _body = {}
        _body.update(test_data_item.get("body", {}))
        _headers = {}
        _headers.update(test_data_item.get("headers", {}))

        # ---- 发送请求 ----
        response = await async_client.request(
            method="POST",
            url="/api/v1/auth/login",
            params=_params if _params else None,
            json=_body if _body else None,
            headers=_headers if _headers else None,
        )

        # ---- 断言 ----
        assert response.status_code == 200, (
            f"状态码不匹配: 预期 200, 实际 {response.status_code}, "
            f"响应: {response.text[:500]}"
        )

        # 数据驱动断言
        _assertions = test_data_item.get("assertions", [])
        for _a in _assertions:
            _do_assertion(response, _a)

    # --------------------------------------------------
    # TC_005: 删除用户
    # --------------------------------------------------
    @pytest.mark.user
    @pytest.mark.delete
    @pytest.mark.p2
    @pytest.mark.asyncio
    async def test_tc_005(self, async_client: httpx.AsyncClient):
        """
        删除用户
        删除指定用户
        优先级: P2
        """
        _params = {}
        _body = {}
        _headers = {}

        # ---- 发送请求 ----
        response = await async_client.request(
            method="DELETE",
            url="/api/v1/users/1",
            params=_params if _params else None,
            headers=_headers if _headers else None,
        )

        # ---- 断言 ----
        assert response.status_code == 204, (
            f"状态码不匹配: 预期 204, 实际 {response.status_code}, "
            f"响应: {response.text[:500]}"
        )

    # --------------------------------------------------
    # TC_006: 用户头像上传
    # --------------------------------------------------
    @pytest.mark.skip(reason="接口尚未上线")
    @pytest.mark.user
    @pytest.mark.p3
    @pytest.mark.asyncio
    async def test_tc_006(self, async_client: httpx.AsyncClient):
        """
        用户头像上传
        上传用户头像（接口开发中）
        优先级: P3
        """
        _params = {}
        _body = {}
        _headers = {}

        # ---- 发送请求 ----
        response = await async_client.request(
            method="POST",
            url="/api/v1/users/avatar",
            params=_params if _params else None,
            json=_body if _body else None,
            headers=_headers if _headers else None,
        )

        # ---- 断言 ----
        assert response.status_code == 200, (
            f"状态码不匹配: 预期 200, 实际 {response.status_code}, "
            f"响应: {response.text[:500]}"
        )

# ============================================
# 辅助函数
# ============================================

def _extract_json_path(data: dict, path: str):
    """简易 JSON Path 提取（支持点号分隔路径，如 data.user.id）"""
    keys = path.replace("$.", "").split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current

def _do_assertion(response: httpx.Response, assertion: dict):
    """执行动态断言（数据驱动场景）"""
    a_type = assertion.get("type", "status_code")
    field = assertion.get("field", "")
    operator = assertion.get("operator", "eq")
    expected = assertion.get("expected")

    if a_type == "status_code":
        actual = response.status_code
    elif a_type == "json_field":
        actual = _extract_json_path(response.json(), field)
    elif a_type == "header":
        actual = response.headers.get(field)
    elif a_type == "contains":
        assert expected in response.text, f"响应体不包含: {expected}"
        return
    else:
        return

    if operator == "eq":
        assert actual == expected, f"断言失败: {field} 预期 {expected}, 实际 {actual}"
    elif operator == "ne":
        assert actual != expected
    elif operator == "gt":
        assert actual > expected
    elif operator == "lt":
        assert actual < expected
    elif operator == "ge":
        assert actual >= expected
    elif operator == "le":
        assert actual <= expected
    elif operator == "contains":
        assert expected in actual
    elif operator == "in":
        assert actual in expected
    elif operator == "not_in":
        assert actual not in expected
