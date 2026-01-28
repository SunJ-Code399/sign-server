# sign-server 签名服务项目免费开源：为通关数据签名提供高效解决方案

在跨境电商和通关业务场景中，数据签名的安全性和可靠性至关重要。为了帮助开发者和企业更便捷地实现数据签名功能，我们决定将自研的签名服务项目 **sign-server** 免费开放。本文将详细介绍该项目的功能特性、部署方法以及使用指南，旨在为有相关需求的用户提供全面的参考。

## 项目概述

**sign-server** 是一款基于 Python Flask 开发的签名与 XML 文件管理服务，主要用于为通关业务系统提供数据签名和文件管理能力。该项目通过 WebSocket 连接海关程序提供的签名服务，实现了与原有 ASP.NET WebService 完全兼容的 HTTP 接口，同时增加了 XML 文件管理功能。

**重要提示**：
- 本项目的 WebSocket 签名接口来源于海关程序，运行前需要先安装海关卡驱动并插入操作员卡
- **本程序只能在 Windows 系统上运行**（必需，因为海关卡驱动只能在 Windows 上运行）

### 核心特点

- **基于 WebSocket 的数字签名**：通过 WebSocket 连接海关程序提供的签名服务，实现数据签名和证书号获取，支持操作员卡硬件加密，确保签名安全可靠
- **AES 加密传输**：所有请求和响应数据使用 AES/ECB/PKCS5Padding 算法加密，确保数据传输安全
- **XML 文件管理**：提供完整的 XML 文件增删查功能，支持自定义目录存储
- **易于部署和使用**：基于 Flask 框架，部署简单，配置灵活
- **完善的错误处理**：提供完整的错误处理和日志记录机制

### 应用场景

- 海关通关管理系统中的数据签名
- 电商平台与通关服务系统的数据交互
- 需要基于操作员卡硬件加密的业务场景
- XML 文件的安全存储和管理

## 部署指南

### 1. 环境准备

在部署签名服务器之前，首先需要准备以下环境：

- **硬件要求**：
  - **CPU**：支持 64 位架构的处理器
  - **内存**：建议至少 4GB RAM，确保服务的流畅运行
  - **存储**：根据 XML 文件存储需求选择合适的硬盘空间
  - **网络**：稳定的网络连接，用于提供 HTTP 服务

- **软件要求**：
  - **操作系统**：Windows 系统（必需，因为海关卡驱动只能在 Windows 上运行）
  - **Python 环境**：Python 3.8 或更高版本（推荐 Python 3.12.2），必须使用 64 位 Python
  - **海关卡驱动**：需要安装海关卡驱动程序（见下方安装说明）
  - **操作员卡**：需要插入操作员卡，程序会自动识别

### 2. 安装 Python（Windows）

如果您还没有安装 Python，可以通过以下方式安装：

**方式一：使用官方安装包（推荐）**

1. 访问 Python 官网下载页面：https://www.python.org/downloads/release/python-3122/
2. 下载 "Windows installer (64-bit)"（**重要**：必须下载 64 位版本）
3. 运行安装程序，**重要**：务必勾选 "Add Python to PATH"
4. 完成安装后，验证安装：
   ```cmd
   python --version
   ```
   应该显示：`Python 3.12.2`

**方式二：使用包管理器**

如果已安装 winget：
```cmd
winget install Python.Python.3.12.2
```

如果已安装 Chocolatey：
```cmd
choco install python312 --version=3.12.2
```

### 3. 安装海关卡驱动（必需）

**重要**：本项目的 WebSocket 签名接口来源于海关程序，运行本程序前必须先安装海关卡驱动。

1. **下载海关卡驱动**：
   - 下载地址：https://update.singlewindow.cn/downloads/EportClientSetup_V1.6.56.exe
   - 下载完成后运行安装程序

2. **插入操作员卡**：
   - 将操作员卡插入电脑
   - 程序会自动识别是否为操作员卡
   - 确保操作员卡已正确连接

3. **验证安装**：
   - 安装完成后，海关程序会自动启动 WebSocket 服务（默认地址：`ws://127.0.0.1:61232`）
   - 确保操作员卡已插入且被正确识别

### 4. 下载与安装项目

1. **获取源码**：从项目仓库下载 **sign-server** 源码

2. **安装项目依赖**：
   ```bash
   pip install -r requirements.txt
   ```
   
   如果遇到网络问题，可以使用国内镜像源：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
   
   如果遇到 `'pip' 不是内部或外部命令` 错误，使用：
   ```bash
   python -m pip install -r requirements.txt
   ```

### 5. 配置说明

编辑项目根目录下的 `config.py` 文件，配置以下参数：

```python
# AES解密密钥（必须与Java端使用的密钥一致）
AES_KEY = "1234567887654321"

# XML文件存储目录
SAVE_FOLDER = "./xml_files/"

# Flask服务配置
HOST = "0.0.0.0"  # 服务监听地址
PORT = 8801        # 服务端口号

# 日志级别
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# WebSocket 签名服务配置
# WebSocket 接口来源于海关程序，需要先安装海关卡驱动并插入操作员卡
# 优先使用本地地址
WS_URL = "ws://127.0.0.1:61232"
```

**重要配置说明**：
- `AES_KEY`：必须与调用方（Java 端）使用的密钥完全一致，否则无法正常加解密
- `PORT`：可以根据实际情况修改服务端口，确保端口未被占用
- `SAVE_FOLDER`：XML 文件存储路径，建议使用绝对路径
- `WS_URL`：WebSocket 签名服务地址，默认使用本地地址 `ws://127.0.0.1:61232`（由海关程序提供）

### 6. 启动服务

在项目根目录下运行：

```bash
python app.py
```

服务启动后，默认在 `http://0.0.0.0:8801` 监听请求。

您也可以通过项目提供的批处理文件启动：

```cmd
start.bat
```

### 7. 验证部署

访问健康检查接口验证服务是否正常运行：

```bash
curl http://localhost:8801/health
```

或直接在浏览器中访问：`http://localhost:8801/health`

正常响应示例：
```json
{
    "code": 200,
    "msg": "服务运行正常",
    "data": true,
    "sign_status": "healthy"
}
```

## 使用指南

### 接口概述

| 接口路径 | 请求方法 | 功能说明 |
|---------|---------|---------|
| `/` | GET | 获取服务信息和所有可用端点 |
| `/health` | GET | 健康检查接口 |
| `/getCode` | POST | WebSocket 签名接口 |
| `/xml-files/add` | POST | 新增 XML 文件 |
| `/xml-files/list` | POST | 查询 XML 文件列表 |
| `/xml-files/delete` | POST | 删除 XML 文件 |

### 加解密规则

所有 POST 接口的请求和响应都使用 AES 加密：

- **算法**：AES/ECB/PKCS5Padding
- **密钥**：使用 `config.AES_KEY` 配置的密钥
- **密文格式**：十六进制字符串
- **字符编码**：UTF-8

### 核心接口说明

#### 1. WebSocket 签名接口：`POST /getCode`

这是项目的核心接口，用于对数据进行数字签名。

**请求体（密文）**：

解密后的 JSON 格式：
```json
{
    "str": "需要加签的数据字符串",
    "pwdstr": "00000000"
}
```

**响应（密文）**：

解密后的 JSON 格式：
```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "sign": "签名字符串",
        "certNo": "证书号字符串"
    }
}
```

响应数据包含 `sign`（签名结果）和 `certNo`（证书号）两个字段。

#### 2. XML 文件管理接口

**新增 XML 文件：`POST /xml-files/add`**

请求体（解密后）：
```json
{
    "filename": "example.xml",
    "xml": "<xml>...</xml>",
    "directory": "/path/optional"
}
```

**查询 XML 文件列表：`POST /xml-files/list`**

请求体（解密后，directory 可选）：
```json
{
    "directory": "/path/optional"
}
```

响应（解密后）：
```json
{
    "code": 200,
    "msg": "查询成功",
    "data": [
        {"filename": "a.xml", "xml": "<xml>...</xml>"},
        {"filename": "b.xml", "xml": "<xml>...</xml>"}
    ]
}
```

**删除 XML 文件：`POST /xml-files/delete`**

请求体（解密后）：
```json
{
    "filename": "example.xml",
    "directory": "/path/optional"
}
```

### 使用示例

#### Python 调用签名接口

```python
import requests
import json
from aes_util import mysql_adapter_encrypt, mysql_adapter_decrypt

# 配置
AES_KEY = "1234567887654321"
url = "http://localhost:8801/getCode"

# 准备请求数据
request_data = {
    "str": "test_data_string",
    "pwdstr": "00000000"
}

# 加密请求数据
plaintext = json.dumps(request_data, ensure_ascii=False)
cipher_text = mysql_adapter_encrypt(AES_KEY, plaintext, encoding="UTF-8")

# 发送请求
response = requests.post(url, data=cipher_text.encode('utf-8'))

# 解密响应
if response.status_code == 200:
    result = response.json()
    encrypted_data = result["data"]
    decrypted_data = mysql_adapter_decrypt(AES_KEY, encrypted_data, encoding="UTF-8")
    data_obj = json.loads(decrypted_data)
    
    # 获取结果
    sign_result = data_obj["sign"]      # 签名结果
    cert_no = data_obj["certNo"]        # 证书号
    print(f"签名: {sign_result}")
    print(f"证书号: {cert_no}")
```

#### Python 调用 XML 文件接口

```python
import requests
import json
from aes_util import mysql_adapter_encrypt, mysql_adapter_decrypt

# 配置
AES_KEY = "1234567887654321"
url = "http://localhost:8801/xml-files/add"

# 准备请求数据
request_data = {
    "filename": "example.xml",
    "xml": "<root><data>test</data></root>"
}

# 加密请求数据
plaintext = json.dumps(request_data, ensure_ascii=False)
cipher_text = mysql_adapter_encrypt(AES_KEY, plaintext, encoding="UTF-8")

# 发送请求
response = requests.post(url, data=cipher_text.encode('utf-8'))
print(response.json())
```

#### 测试脚本

项目提供了 `test_sign64_http_service.py` 测试脚本，用于测试 `/getCode` 接口的功能。

**功能说明**：
- 测试 WebSocket 签名接口的完整调用流程
- 演示如何加密请求数据、发送请求、解密响应数据
- 验证签名结果和证书号的正确性
- 提供详细的测试输出和错误信息

**使用方法**：

1. **确保服务已启动**：
   - 启动 Flask 服务：`python app.py`
   - 确保海关程序已启动，WebSocket 服务正常运行（`ws://127.0.0.1:61232`）
   - 确保操作员卡已插入

2. **运行测试脚本**：
   ```bash
   python test_sign64_http_service.py
   ```

3. **测试流程**：
   - 脚本会提示按回车键开始测试
   - 自动加密测试数据并发送请求
   - 解密响应并验证结果格式
   - 输出详细的测试过程和结果

> **注意**: 运行测试前，请确保服务已启动（`python app.py`），并且 WebSocket 签名服务已启动并可访问。

### 系统集成流程示例

以下展示了签名服务在通关数据交互流程中的典型使用场景：

**流程说明**：

1. 海关通关管理系统向通关服务系统发起数据获取请求（包含订单号等信息）
2. 通关服务系统调用电商平台系统的 `platDataOpen` 接口
3. 电商平台系统返回接收成功（code=10000）
4. 电商平台系统内部组织支付数据（查询订单支付信息）
5. **电商平台系统调用签名服务系统的 `/getCode` 接口，对支付数据进行加签**
6. 签名服务系统返回签名结果（签名+证书号）
7. 电商平台系统调用通关服务系统的 `realTimeDataUpload` 接口，携带支付数据和签名
8. 通关服务系统返回接收结果（code=10000）
9. 通关服务系统将支付数据转发给海关通关管理系统

**关键点**：签名服务在电商平台系统调用 `realTimeDataUpload` 接口之前被调用，确保数据在传输前已完成数字签名。

## 技术架构

### 项目结构

```
sign-server/
├── app.py                  # Flask应用主文件（统一入口）
├── config.py               # 配置文件
├── websocket_wrapper.py    # WebSocket 签名服务的 Python 封装
├── aes_util.py             # AES加解密工具（Java兼容）
├── services/
│   └── xml_service.py      # XML文件业务逻辑
├── xml_files/              # XML文件存储目录（自动创建）
├── test_sign64_http_service.py  # 签名服务测试脚本
└── requirements.txt        # Python依赖
```

### 技术栈

- **Web 框架**：Flask 3.0+
- **加密库**：pycryptodome（提供 AES 加解密功能）
- **WebSocket 客户端**：websockets（连接签名服务）
- **签名服务**：通过 WebSocket 连接海关程序提供的签名服务

### getCode 接口逻辑梳理

#### 整体架构

```
HTTP 请求 (POST /getCode)
    ↓
Flask 接口层 (app.py: getcode())
    ↓
WebSocket 包装层 (websocket_wrapper.py: get_code())
    ↓
异步处理层 (websocket_wrapper.py: _get_sign_async())
    ↓
WebSocket 通信层 (websocket_wrapper.py: _get_sign_with_connection())
    ↓
WebSocket 服务器 (ws://127.0.0.1:61232/)
```

#### 详细流程

**1. Flask 接口层 (`app.py: getcode()`)**

- **服务可用性检查**：检查 WebSocket 服务是否已初始化
- **请求解密与验证**：使用 AES 解密请求体，验证是否为 JSON 对象
- **参数提取与验证**：提取 `str`（待签名数据）和 `pwdstr`（密码），验证必需字段和类型
- **调用签名服务**：调用 WebSocket 包装层的 `get_code()` 方法，返回格式：`"签名字符串||证书序列号"`
- **结果解析与响应**：按 `||` 分隔符拆分结果，验证两部分都有值，使用 AES 加密响应数据，返回 JSON 格式的加密响应
- **异常处理**：`ValueError` → 400，`WebSocketError` → 500，其他异常 → 500

**2. WebSocket 包装层 (`websocket_wrapper.py: get_code()`)**

- **输入验证**：检查参数类型和空值
- **线程锁保护**：使用 `threading.Lock()` 确保同一时间只有一个请求在执行
- **服务可用性检查**：检查 WebSocket 服务是否已正确初始化
- **事件循环管理**：获取或创建事件循环，用于运行异步函数
- **执行异步函数**：在事件循环中运行 `_get_sign_async()` 并等待结果
- **结果验证与格式化**：验证签名和证书序列号都不为空，返回 `"签名字符串||证书序列号"` 格式

**3. 异步处理层 (`websocket_wrapper.py: _get_sign_async()`)**

- **重试机制**：连接错误时最多重试 1 次（总共尝试 2 次）
- **连接管理**：确保 WebSocket 连接可用，如果连接不存在或不可用则创建新连接
- **执行签名请求**：调用 `_get_sign_with_connection()` 执行实际的签名请求

**4. 连接管理 (`websocket_wrapper.py: _ensure_connection()`)**

- **连接复用检查**：如果已有可用连接则直接复用
- **创建新连接**：根据 URL 判断是否需要 SSL（`wss://` 需要，`ws://` 不需要）
- **握手处理**：接收并验证握手消息（`_method` 应为 `"open"`），握手失败则关闭连接
- **保存连接状态**：握手成功后保存连接对象和状态

**5. WebSocket 通信层 (`websocket_wrapper.py: _get_sign_with_connection()`)**

- **构建请求**：
  ```json
  {
      "_id": "1",
      "_method": "cus-sec_SpcSignDataAsPEM",
      "args": {
          "inData": "待签名数据",
          "passwd": "密码"
      }
  }
  ```
- **发送请求**：通过 WebSocket 发送 JSON 格式的请求
- **接收响应（带超时）**：设置 30 秒超时，防止请求无限期挂起
- **解析响应**：支持两种响应格式：
  - **嵌套格式**：`{"_id": 1, "_method": "...", "_status": "00", "_args": {"Result": true, "Data": ["签名", "证书号"], "Error": []}}`
  - **直接格式**：`{"Result": true, "Data": ["签名", "证书号"], "Error": []}`
- **响应验证**：检查状态码（`_status` 应为 `"00"`）、结果（`Result` 应为 `true`）和数据（`Data` 数组应包含至少 1 个元素）
- **异常处理**：`ConnectionClosed`、`WebSocketException`、`JSONDecodeError`、`TimeoutError` 等

#### 数据流

```
客户端请求（AES 密文）
    ↓
解密 → {"str": "数据", "pwdstr": "密码"}
    ↓
WebSocket 请求 → {"_id": "1", "_method": "cus-sec_SpcSignDataAsPEM", "args": {...}}
    ↓
WebSocket 响应 → {"_status": "00", "_args": {"Result": true, "Data": ["签名", "证书号"]}}
    ↓
解析 → {"sign": "签名", "cert_no": "证书号"}
    ↓
格式化 → "签名字符串||证书序列号"
    ↓
拆分 → {"sign": "签名", "certNo": "证书号"}
    ↓
加密 → AES 密文
    ↓
响应 → {"code": 200, "msg": "成功", "data": "密文"}
```

#### 关键设计点

1. **连接复用策略**：维护单个 WebSocket 连接，在多个请求间复用，减少连接建立开销
2. **线程安全**：使用 `threading.Lock()` 确保同一时间只有一个请求在执行，避免数据串流
3. **事件循环管理**：创建独立的事件循环，使用 `run_until_complete()` 执行异步函数
4. **重试机制**：连接错误时最多重试 1 次，平衡可靠性和性能
5. **超时控制**：30 秒接收超时，防止请求无限期挂起
6. **握手验证**：验证 WebSocket 服务器发送的握手消息，确保连接正常建立

## 常见问题

### 1. 'pip' 不是内部或外部命令

**原因**：Python 未添加到 PATH 环境变量，或 pip 未正确安装。

**解决方法**：
- **推荐**：使用 `python -m pip` 代替 `pip`
  ```bash
  python -m pip install -r requirements.txt
  ```
- 检查 Python 是否安装：`python --version`
- 如果 Python 未安装，重新安装并勾选 "Add Python to PATH"
- 如果 Python 已安装但 pip 不可用：`python -m ensurepip --upgrade`

### 2. WebSocket 连接失败

**原因**：WebSocket 签名服务未启动或地址配置错误。

**解决方法**：
- 确保已安装海关卡驱动并插入操作员卡（见安装说明）
- 确保海关程序已启动，WebSocket 服务正常运行（默认地址：`ws://127.0.0.1:61232`）
- 检查 `config.py` 中的 `WS_URL` 配置是否正确
- 检查网络连接和防火墙设置
- 查看日志文件了解详细错误信息

### 3. 签名服务调用失败

**原因**：WebSocket 服务异常、操作员卡未连接或参数不正确。

**解决方法**：
- 检查 WebSocket 签名服务是否正常运行
- 确保操作员卡已正确插入
- 确认 `pwdstr` 参数是否正确
- 查看日志文件了解详细错误信息

### 4. AES 解密失败

**原因**：密钥不一致或密文格式错误。

**解决方法**：
- 确保 `config.AES_KEY` 与客户端使用的密钥完全一致
- 检查密文是否为十六进制字符串格式
- 确认加密算法为 AES/ECB/PKCS5Padding

### 5. 批处理文件（.bat）无法运行

**原因**：批处理文件编码格式不正确。Windows 批处理文件必须使用 ANSI/GBK 编码，不能使用 UTF-8 编码。

**解决方法**：

如果 `start.bat`、`stop.bat` 或 `view_log.bat` 无法正常运行，请按以下步骤修复文件编码：

1. **用 Windows 记事本打开批处理文件**（如 `start.bat`）
2. **选择"另存为"**
3. **在"编码"下拉框中选择"ANSI"**（不是 UTF-8）
4. **保存文件**（可以覆盖原文件或另存为新文件）
5. **重复以上步骤处理其他 .bat 文件**（`stop.bat`、`view_log.bat`）

**说明**：
- Windows 批处理文件（.bat）默认使用 ANSI/GBK 编码
- 如果文件被保存为 UTF-8 编码，Windows 可能无法正确解析和执行
- 使用记事本另存为 ANSI 编码可以解决此问题

## 注意事项

1. **平台要求**：
   - 本程序只能在 Windows 系统上运行（必需，因为海关卡驱动只能在 Windows 上运行）
   - 必须使用 64 位 Python（因为海关卡驱动是 64 位的）
   - 确保 Windows 系统已正确安装并配置

2. **WebSocket 签名服务**：
   - WebSocket 接口来源于海关程序，需要先安装海关卡驱动并插入操作员卡
   - 下载安装海关卡驱动：https://update.singlewindow.cn/downloads/EportClientSetup_V1.6.56.exe
   - 插入操作员卡，程序会自动识别是否为操作员卡
   - 安装完成后，海关程序会自动启动 WebSocket 服务（默认地址：`ws://127.0.0.1:61232`）
   - 在 `config.py` 中配置 `WS_URL` 为 `ws://127.0.0.1:61232`（优先使用本地地址）

3. **编码**：
   - 请求和响应都使用 UTF-8 编码
   - JSON 格式传输

4. **加密传输**：
   - 所有 POST 接口的请求和响应都使用 AES 加密
   - 确保 `AES_KEY` 配置与客户端一致

5. **文件管理**：
   - 文件名会自动添加 `.xml` 扩展名（如果未提供）
   - 文件名中的路径分隔符会被自动清理，防止路径遍历攻击

6. **连接复用**：
   - WebSocket 连接支持复用，提高性能
   - 连接失败时会自动重试

## 项目优势

相比原有的 ASP.NET WebService 实现，**sign-server** 具有以下优势：

1. **轻量级部署**：基于 Python Flask，无需安装 IIS 等重量级服务器
2. **Windows 原生支持**：基于 Windows 平台，与海关卡驱动完美集成
3. **易于维护**：Python 代码简洁易读，便于后续维护和功能扩展
4. **配置灵活**：通过配置文件轻松调整服务参数
5. **完善的日志**：提供详细的日志记录，便于问题排查
6. **服务解耦**：签名服务通过 WebSocket 独立部署，便于扩展和维护

## 结语

通过免费开放 **sign-server** 项目，我们希望为开发者和企业提供一个高效、安全的数据签名解决方案，特别是在通关业务和数据安全领域。项目完全开源，大家可以自由使用、修改和分发。

我们欢迎广大开发者：
- 下载、使用并提出宝贵的意见和建议
- 参与项目的改进和优化
- 提交 issue 报告问题或提出功能需求
- Fork 项目并贡献代码

希望 **sign-server** 能为您的项目带来价值，助力数据安全的实现。如果项目对您有帮助，欢迎 Star 支持！

---

**项目地址**：[https://github.com/SunJ-Code399/sign-server]

**技术支持**：如有任何问题，请通过项目的 Issues 页面提交，我们将及时跟进和解答。

**技术咨询**：17744405157（微信）

**许可证**：本项目采用开源许可证，可自由使用。
