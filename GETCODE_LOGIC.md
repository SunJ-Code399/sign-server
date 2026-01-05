# getCode 接口逻辑梳理

## 整体架构

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

---

## 详细流程

### 1. Flask 接口层 (`app.py: getcode()`)

#### 1.1 服务可用性检查
```python
if not sign_service.is_available():
    return 500 错误
```
- 检查 WebSocket 服务是否已初始化
- 实际检查：`ws_url` 是否存在

#### 1.2 请求解密与验证
```python
raw_body = request.get_data()  # 获取原始密文
request_data = decrypt_request_body(raw_body, config.AES_KEY, encoding="UTF-8")
```
- **解密**：使用 AES 解密请求体
- **验证**：检查是否为 JSON 对象

#### 1.3 参数提取与验证
```python
str_data = request_data.get("str")      # 待签名数据
pwdstr = request_data.get("pwdstr")     # 密码
```
- **必需字段检查**：`str` 和 `pwdstr` 必须存在
- **类型检查**：两者必须是字符串类型

#### 1.4 调用签名服务
```python
result = sign_service.get_code(str_data, pwdstr)
```
- 调用 WebSocket 包装层的 `get_code()` 方法
- 返回格式：`"签名字符串||证书序列号"`

#### 1.5 结果解析与响应
```python
if "||" in result:
    parts = result.split("||", 1)  # 只分割一次
    sign = parts[0].strip()
    cert_no = parts[1].strip()
    
    response_data = {
        "sign": sign,
        "certNo": cert_no
    }
    resp_data = encrypt_response_data(response_data, config.AES_KEY)  # 加密响应
    return jsonify({"code": 200, "msg": "成功", "data": resp_data})
```
- **拆分结果**：按 `||` 分隔符拆分
- **验证**：确保两部分都有值
- **加密响应**：使用 AES 加密响应数据
- **返回**：JSON 格式的加密响应

#### 1.6 异常处理
- `ValueError`：解密失败或数据格式错误 → 400
- `WebSocketError`：WebSocket 相关错误 → 500
- `Exception`：其他异常 → 500

---

### 2. WebSocket 包装层 (`websocket_wrapper.py: get_code()`)

#### 2.1 输入验证（第一层）
```python
# 参数类型和空值检查
if not isinstance(data, str) or not isinstance(pwdstr, str):
    raise WebSocketError("参数类型错误")
if not data or not pwdstr:
    raise WebSocketError("参数不能为空")
```

#### 2.2 线程锁保护
```python
with self.lock:
    # 所有后续操作都在锁内执行
```
- **目的**：确保同一时间只有一个请求在执行
- **作用**：防止并发请求导致数据串流

#### 2.3 服务可用性检查（第二层）
```python
if not self.is_available():
    raise WebSocketError("WebSocket 服务未正确初始化")
```

#### 2.4 事件循环管理
```python
loop = self._get_or_create_loop()
```
- **逻辑**：
  1. 尝试获取当前运行的事件循环
  2. 如果已有运行中的循环 → 抛出异常（不能使用 `run_until_complete`）
  3. 如果没有运行中的循环 → 创建或复用现有循环

#### 2.5 执行异步函数
```python
result = loop.run_until_complete(self._get_sign_async(data, pwdstr))
```
- 在事件循环中运行异步函数
- 等待异步函数完成并返回结果

#### 2.6 结果验证与格式化
```python
sign = result.get("sign")
cert_no = result.get("cert_no")

if not sign:
    raise WebSocketError("签名结果为空")
if not cert_no:
    raise WebSocketError("证书序列号为空")

return f"{sign}||{cert_no}"
```
- 验证签名和证书序列号都不为空
- 返回 `"签名字符串||证书序列号"` 格式

---

### 3. 异步处理层 (`websocket_wrapper.py: _get_sign_async()`)

#### 3.1 重试机制
```python
max_retries = 1  # 最多重试1次（总共尝试2次）

for retry in range(max_retries + 1):
    try:
        # 执行签名请求
    except WebSocketError as e:
        if "连接" in str(e) and retry < max_retries:
            # 连接错误时重试
            continue
        else:
            raise
```

#### 3.2 连接管理
```python
websocket = await self._ensure_connection()
```
- 确保 WebSocket 连接可用
- 如果连接不存在或不可用，创建新连接

#### 3.3 执行签名请求
```python
return await self._get_sign_with_connection(websocket, in_data, passwd)
```

---

### 4. 连接管理 (`websocket_wrapper.py: _ensure_connection()`)

#### 4.1 连接复用检查
```python
if self.connected and self.websocket:
    return self.websocket  # 复用现有连接
```

#### 4.2 创建新连接
```python
# 根据 URL 判断是否需要 SSL
if self.ws_url.startswith("wss://"):
    websocket = await websockets.connect(self.ws_url, ssl=True)
else:
    websocket = await websockets.connect(self.ws_url)
```

#### 4.3 握手处理
```python
handshake_success = await self._handle_handshake(websocket)
if not handshake_success:
    await websocket.close()
    raise WebSocketError("WebSocket 握手失败")
```
- **握手消息格式**：`{"_id":0,"_method":"open","_status":"00",...}`
- **验证**：检查 `_method` 是否为 `"open"`
- **失败处理**：关闭连接并抛出异常

#### 4.4 保存连接状态
```python
self.websocket = websocket
self.connected = True
```

---

### 5. WebSocket 通信层 (`websocket_wrapper.py: _get_sign_with_connection()`)

#### 5.1 构建请求
```python
request = {
    "_id": "1",
    "_method": "cus-sec_SpcSignDataAsPEM",
    "args": {
        "inData": in_data,
        "passwd": passwd
    }
}
request_json = json.dumps(request)
```

#### 5.2 发送请求
```python
await websocket.send(request_json)
```

#### 5.3 接收响应（带超时）
```python
response_json = await asyncio.wait_for(websocket.recv(), timeout=30.0)
```
- **超时时间**：30 秒
- **超时处理**：抛出 `WebSocketError("接收响应超时（30秒）")`

#### 5.4 解析响应

**支持两种响应格式：**

**格式1：嵌套格式**
```json
{
    "_id": 1,
    "_method": "cus-sec_SpcSignDataAsPEM",
    "_status": "00",
    "_args": {
        "Result": true,
        "Data": ["签名字符串", "证书序列号"],
        "Error": []
    }
}
```

**格式2：直接格式**
```json
{
    "Result": true,
    "Data": ["签名字符串", "证书序列号"],
    "Error": []
}
```

#### 5.5 响应验证
```python
# 检查状态码
if status and status != "00":
    raise WebSocketError("响应状态错误")

# 检查结果
if not result:
    raise WebSocketError("签名失败")

# 检查数据
if data and len(data) >= 2:
    sign = data[0]
    cert_no = data[1]
    return {"sign": sign, "cert_no": cert_no}
elif data and len(data) == 1:
    sign = data[0]
    return {"sign": sign, "cert_no": None}
else:
    raise WebSocketError("响应中未找到 Data 字段或 Data 为空")
```

#### 5.6 异常处理
- `ConnectionClosed`：连接已关闭 → 标记连接不可用，抛出异常
- `WebSocketException`：WebSocket 错误 → 标记连接不可用，抛出异常
- `JSONDecodeError`：JSON 解析错误 → 抛出异常
- `TimeoutError`：接收超时 → 抛出异常

---

## 关键设计点

### 1. 连接复用策略
- **目标**：减少连接建立开销，提高性能
- **实现**：维护单个 WebSocket 连接，在多个请求间复用
- **失效处理**：连接失败时自动重新创建

### 2. 线程安全
- **问题**：Flask 是多线程环境，WebSocket 连接是共享资源
- **解决**：使用 `threading.Lock()` 确保同一时间只有一个请求在执行
- **影响**：请求会串行执行，但避免了数据串流问题

### 3. 事件循环管理
- **问题**：Flask 是同步框架，需要运行异步代码
- **解决**：创建独立的事件循环，使用 `run_until_complete()` 执行异步函数
- **限制**：不能在已有运行循环的线程中使用

### 4. 重试机制
- **策略**：连接错误时最多重试 1 次
- **范围**：仅对连接相关错误重试，其他错误直接抛出

### 5. 超时控制
- **接收超时**：30 秒
- **目的**：防止请求无限期挂起

### 6. 握手验证
- **必要性**：WebSocket 服务器在连接后立即发送握手消息
- **验证**：检查握手消息的 `_method` 是否为 `"open"`
- **失败处理**：关闭连接，不保存连接状态

---

## 数据流

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

---

## 错误处理链

```
WebSocket 通信错误
    ↓
WebSocketError (websocket_wrapper.py)
    ↓
捕获并返回 500 (app.py)
    ↓
{"code": 500, "msg": "错误信息", "data": False}
```

---

## 性能考虑

1. **连接复用**：减少连接建立开销
2. **串行执行**：锁保护导致请求串行，可能成为瓶颈
3. **超时控制**：30 秒超时防止资源占用
4. **重试机制**：最多重试 1 次，平衡可靠性和性能

---

## 潜在改进点

1. **请求ID唯一性**：当前使用固定 `_id: "1"`，虽然有锁保护，但理论上应该使用唯一ID
2. **连接健康检查**：可以定期检查连接是否真的可用
3. **连接池**：如果需要更高并发，可以考虑连接池
4. **异步接口**：提供异步版本的 `get_code()` 方法，避免事件循环冲突

