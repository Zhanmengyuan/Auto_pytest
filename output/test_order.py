"""
自动生成的接口测试文件
模块: order
生成时间: 2026-03-04 11:05:16
"""

import json
import pytest
import httpx
import pytest_asyncio

class TestOrder:
    """order 模块接口测试"""

    # --------------------------------------------------
    # TC_004: 创建订单
    # --------------------------------------------------
    @pytest.mark.order
    @pytest.mark.p1
    @pytest.mark.asyncio
    async def test_tc_004(self, async_client: httpx.AsyncClient):
        """
        创建订单
        先登录获取 token，再创建订单
        优先级: P1
        """
        # ---- 前置操作 ----
        _extracted = {}
        # 前置步骤: 登录获取token
        _setup_resp_1 = await async_client.request(
            method="POST",
            url="/api/v1/auth/login",
            headers={},
            json={"username": "admin", "password": "123456"},
        )
        _setup_data_1 = _setup_resp_1.json()
        _extracted["token"] = _extract_json_path(_setup_data_1, "data.token")

        _params = {}
        _body = {"product_id": 1001, "quantity": 2}
        _headers = {}

        # ---- 发送请求 ----
        response = await async_client.request(
            method="POST",
            url="/api/v1/orders",
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

        # 断言: JSON 字段 data.order_id ne 
        _resp_json = response.json()
        _actual_val = _extract_json_path(_resp_json, "data.order_id")
        assert _actual_val != ""

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
