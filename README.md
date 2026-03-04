# Auto Pytest — 功能用例自动转换为接口自动化测试用例

一个将 **YAML 格式的功能用例** 自动生成为 **pytest + httpx 自动化接口测试代码** 的转换系统。

## 核心特性

| 特性 | 说明 |
|------|------|
| **YAML 数据驱动** | 结构化 YAML 描述用例，天然支持嵌套，告别 JSON 字符串 |
| **pytest + httpx** | 异步/同步双模式客户端 |
| **数据驱动** | 同一接口支持多组测试数据参数化 |
| **多环境配置** | dev / test / prod 一键切换 |
| **前置步骤** | 支持接口依赖、Token提取等 |
| **丰富断言** | 状态码、JSON字段、响应头、包含等 |
| **优先级标签** | P0~P3 优先级 + 自定义标签 |
| **批量解析** | 支持单文件或整目录扫描 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化项目

```bash
python main.py init
```

### 3. 生成示例用例模板

```bash
python main.py sample
```

这会在 `testcases/sample_cases.yaml` 生成一个预填充示例的 YAML 文件。

### 4. 编辑功能用例

打开 YAML 文件，按照格式填写你的功能用例。

### 5. 生成测试代码

```bash
# 单文件
python main.py generate -i testcases/sample_cases.yaml -o output/

# 整目录（解析目录下所有 .yaml 文件）
python main.py generate -d testcases/ -o output/
```

### 6. 运行测试

```bash
cd output
pytest -v --env=dev                # 开发环境
pytest -v --env=test               # 测试环境
pytest -v --env=dev -m p0          # 仅运行 P0 用例
pytest -v --env=dev -m "smoke"     # 仅运行 smoke 标签
```

## YAML 用例格式

```yaml
# (可选) 全局默认配置，被所有用例继承
global_config:
  is_async: true
  content_type: "application/json"

cases:
  # ---- 基本 GET 请求 ----
  - case_id: TC_001
    module: user
    title: 获取用户列表
    priority: P0
    tags: [smoke, user]
    method: GET
    path: /api/v1/users
    params:
      page: 1
      size: 10
    expected_status: 200
    assertions:
      - type: json_field
        field: code
        operator: eq
        expected: 0

  # ---- POST 创建资源 ----
  - case_id: TC_002
    module: user
    title: 创建新用户
    method: POST
    path: /api/v1/users
    body:
      name: 张三
      email: zhangsan@test.com
    expected_status: 201
    assertions:
      - type: json_field
        field: data.name
        operator: eq
        expected: 张三

  # ---- 数据驱动（参数化多场景）----
  - case_id: TC_003
    module: user
    title: 用户登录-多场景
    method: POST
    path: /api/v1/auth/login
    expected_status: 200
    test_data:
      - name: 正常登录
        body: { username: admin, password: "123456" }
        assertions:
          - { type: json_field, field: data.token, operator: ne, expected: "" }
      - name: 密码错误
        body: { username: admin, password: wrong }
        assertions:
          - { type: json_field, field: code, operator: eq, expected: 401 }

  # ---- 带前置步骤（接口依赖）----
  - case_id: TC_004
    module: order
    title: 创建订单
    method: POST
    path: /api/v1/orders
    body: { product_id: 1001, quantity: 2 }
    expected_status: 201
    setup_steps:
      - description: 登录获取token
        method: POST
        url: /api/v1/auth/login
        body: { username: admin, password: "123456" }
        extract: { token: data.token }
```

### 完整字段参考

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `case_id` | ✅ | str | 唯一标识，如 TC_001 |
| `module` | ✅ | str | 所属模块（按模块分文件） |
| `title` | ✅ | str | 用例标题 |
| `description` | | str | 详细说明 |
| `priority` | | str | P0/P1/P2/P3，默认 P1 |
| `tags` | | list | 标签列表 |
| `method` | ✅ | str | GET/POST/PUT/DELETE/PATCH |
| `path` | ✅ | str | 接口路径 |
| `headers` | | dict | 自定义请求头 |
| `params` | | dict | Query 参数 |
| `body` | | dict | 请求体 |
| `content_type` | | str | Content-Type，默认 application/json |
| `setup_steps` | | list | 前置操作步骤 |
| `depends_on` | | list | 依赖用例编号 |
| `expected_status` | | int | 预期状态码，默认 200 |
| `assertions` | | list | 断言列表 |
| `test_data` | | list | 数据驱动测试数据 |
| `is_async` | | bool | 是否异步，默认 true |
| `skip` | | bool | 是否跳过 |
| `skip_reason` | | str | 跳过原因 |

### 断言格式

```yaml
assertions:
  - type: json_field      # status_code / json_field / header / contains
    field: data.user.name  # 字段路径（点号分隔）
    operator: eq           # eq / ne / gt / lt / ge / le / in / not_in / contains
    expected: "张三"       # 期望值
```

### 前置步骤格式

```yaml
setup_steps:
  - description: 登录获取token
    method: POST
    url: /api/v1/auth/login
    body:
      username: admin
      password: "123456"
    extract:
      token: data.token    # 从响应中提取变量
```

### 数据驱动格式

```yaml
test_data:
  - name: 场景一-正常
    body: { username: admin, password: "123456" }
    assertions:
      - { type: json_field, field: data.token, operator: ne, expected: "" }
  - name: 场景二-异常
    body: { username: admin, password: wrong }
    assertions:
      - { type: json_field, field: code, operator: eq, expected: 401 }
```

## 多环境配置

编辑 `config/env_config.yaml`:

```yaml
active_env: dev

environments:
  dev:
    base_url: "http://localhost:8080"
    timeout: 30
    headers:
      Content-Type: "application/json"
    auth:
      type: "bearer"
      token: "dev-token-xxx"

  test:
    base_url: "https://test-api.example.com"
    timeout: 30
    auth:
      type: "bearer"
      token: "test-token-xxx"
```

## 项目结构

```
auto_pytest/
├── main.py                        # CLI 入口
├── requirements.txt               # 依赖
├── config/
│   └── env_config.yaml            # 多环境配置
├── templates/
│   └── test_template.py.j2        # 代码生成模板
├── testcases/                     # YAML 功能用例
│   ├── sample_cases.yaml          # 示例用例
│   ├── user.yaml                  # 按模块拆分…
│   └── order.yaml
├── src/
│   ├── models/
│   │   └── test_case.py           # 数据模型
│   ├── parser/
│   │   └── yaml_parser.py         # YAML 解析器
│   ├── generator/
│   │   └── test_generator.py      # 测试代码生成器
│   └── utils/
│       └── helpers.py             # 工具函数
└── output/                        # 生成的测试代码
    ├── conftest.py
    └── test_xxx.py
```

## 工作流程

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  YAML 用例文件    │────▶│  YAML 解析器      │────▶│  TestCase 模型   │
│  (结构化功能用例)  │     │  (自动解析嵌套)    │     │  (Pydantic 校验) │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  pytest 测试代码  │◀────│  生成器 Generator │◀────│ Jinja2 模板引擎   │
│  (可直接运行)     │     │  (按模块分文件)    │     │ (代码模板渲染)    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```
