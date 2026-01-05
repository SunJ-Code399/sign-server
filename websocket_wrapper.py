# -*- coding: utf-8 -*-
"""
WebSocket 签名服务封装

提供与 Sign64Wrapper 相同的接口，但使用 WebSocket 方式获取签名和证书序列号。
使用连接复用策略：维护一个连接，可用时复用，不可用时创建新连接。
"""
import asyncio
import json
import logging
import threading
import websockets
from typing import Optional

logger = logging.getLogger(__name__)


class WebSocketError(RuntimeError):
    """WebSocket 相关错误"""


class WebSocketWrapper:
    """WebSocket 签名服务的 Python 封装（连接复用）"""

    def __init__(self, ws_url: Optional[str] = None) -> None:
        """
        初始化 WebSocket 包装器
        
        Args:
            ws_url: WebSocket 服务器地址，如果为 None 则从 config 导入
        """
        if ws_url is None:
            try:
                import config
                ws_url = config.WS_URL
            except (ImportError, AttributeError):
                ws_url = "ws://127.0.0.1:61232/"
        
        self.ws_url = ws_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.lock = threading.Lock()  # 用于保护 get_code 方法的并发访问
        logger.info(f"WebSocketWrapper 初始化，服务器地址: {self.ws_url}")

    def is_available(self) -> bool:
        """
        检查 WebSocket 服务是否可用
        
        Returns:
            bool: 总是返回 True（连接在调用时创建）
        """
        return bool(self.ws_url)

    async def _handle_handshake(self, websocket) -> bool:
        """
        处理 WebSocket 握手消息
        
        Args:
            websocket: WebSocket 连接对象
            
        Returns:
            bool: 握手是否成功
        """
        try:
            handshake_json = await websocket.recv()
            logger.debug(f"收到握手消息: {handshake_json}")
            
            # 解析握手消息
            handshake = json.loads(handshake_json)
            method = handshake.get("_method")
            if method == "open":
                logger.debug("握手成功")
                return True
            else:
                logger.warning(f"收到非预期的握手消息，方法: {method}")
                return False
        except Exception as e:
            logger.error(f"处理握手消息失败: {e}")
            return False

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """
        获取或创建事件循环
        
        Returns:
            asyncio.AbstractEventLoop: 事件循环对象
        """
        try:
            # 尝试获取当前运行的事件循环
            loop = asyncio.get_running_loop()
            # 如果已有运行中的循环，不能使用 run_until_complete
            # 这种情况下需要抛出异常，提示使用异步方式
            raise RuntimeError("当前线程已有运行中的事件循环，无法使用 run_until_complete")
        except RuntimeError:
            # 没有运行中的循环，可以创建或使用现有循环
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
            return self.loop

    async def _ensure_connection(self) -> websockets.WebSocketClientProtocol:
        """
        确保连接可用，如果不可用则创建新连接
        
        Returns:
            websockets.WebSocketClientProtocol: WebSocket 连接对象
            
        Raises:
            WebSocketError: 当连接失败时
        """
        # 检查现有连接是否可用（简单检查，实际使用时如果不可用会抛出异常）
        if self.connected and self.websocket:
            return self.websocket
        
        # 连接不存在或不可用，需要创建新连接
        self.connected = False
        self.websocket = None
        
        # 创建新连接
        try:
            logger.debug(f"正在连接 WebSocket 服务器: {self.ws_url}")
            # 根据 URL 判断是否需要 SSL（ws:// 不需要，wss:// 需要）
            if self.ws_url.startswith("wss://"):
                # wss:// 需要 SSL
                websocket = await websockets.connect(
                    self.ws_url,
                    ssl=True
                )
            else:
                # ws:// 不需要 SSL，不传递 ssl 参数
                websocket = await websockets.connect(
                    self.ws_url
                )
            logger.debug("WebSocket 连接成功")
            
            # 接收握手消息，如果握手失败则抛出异常
            handshake_success = await self._handle_handshake(websocket)
            if not handshake_success:
                await websocket.close()
                raise WebSocketError("WebSocket 握手失败")
            
            # 保存连接（只有在握手成功后才保存）
            self.websocket = websocket
            self.connected = True
            logger.debug("连接已建立并准备就绪")
            
            return websocket
        except Exception as e:
            self.connected = False
            self.websocket = None
            error_msg = f"连接 WebSocket 失败: {e}"
            logger.error(error_msg)
            raise WebSocketError(error_msg)

    async def _get_sign_with_connection(
        self, 
        websocket: websockets.WebSocketClientProtocol,
        in_data: str, 
        passwd: str
    ) -> dict:
        """
        使用指定连接获取签名和证书序列号
        
        Args:
            websocket: WebSocket 连接对象
            in_data: 待签名的数据字符串
            passwd: 密码
            
        Returns:
            dict: 包含 sign (签名) 和 cert_no (证书序列号) 的字典
            
        Raises:
            WebSocketError: 当 WebSocket 调用失败时
        """
        try:
            # 构建获取签名的请求报文
            request = {
                "_id": "1",
                "_method": "cus-sec_SpcSignDataAsPEM",
                "args": {
                    "inData": in_data,
                    "passwd": passwd
                }
            }
            request_json = json.dumps(request)
            
            logger.debug(f"发送签名请求")
            
            # 发送请求
            await websocket.send(request_json)
            
            # 接收签名响应（设置30秒超时）
            try:
                response_json = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                logger.debug(f"收到响应")
            except asyncio.TimeoutError:
                raise WebSocketError("接收响应超时（30秒）")
            
            # 解析响应
            response = json.loads(response_json)
            
            # 检查响应格式（支持嵌套格式）
            if "_args" in response:
                # 嵌套格式：{"_id":1,"_method":"...","_status":"00","_args":{"Result":true,"Data":["签名","证书序列号"],"Error":[]}}
                args = response.get("_args", {})
                result = args.get("Result")
                data = args.get("Data", [])
                errors = args.get("Error", [])
                status = response.get("_status")
                
                if status and status != "00":
                    error_msg = f"响应状态错误: {status}, 错误信息: {errors}"
                    logger.error(error_msg)
                    raise WebSocketError(error_msg)
                
                if not result:
                    error_msg = f"签名失败，错误信息: {errors}"
                    logger.error(error_msg)
                    raise WebSocketError(error_msg)
                
                if data and len(data) >= 2:
                    sign = data[0]  # 签名字符串
                    cert_no = data[1]  # 证书序列号
                    logger.debug(f"签名成功，签名长度: {len(sign)}, 证书序列号: {cert_no}")
                    return {
                        "sign": sign,
                        "cert_no": cert_no
                    }
                elif data and len(data) == 1:
                    sign = data[0]
                    logger.warning(f"签名成功（无证书序列号），签名长度: {len(sign)}")
                    return {
                        "sign": sign,
                        "cert_no": None
                    }
                else:
                    error_msg = "响应中未找到 Data 字段或 Data 为空"
                    logger.error(f"{error_msg}: {response}")
                    raise WebSocketError(error_msg)
            elif "Result" in response:
                # 直接格式：{"Result":true,"Data":["签名","证书序列号"],"Error":[]}
                result = response.get("Result")
                data = response.get("Data", [])
                errors = response.get("Error", [])
                
                if not result:
                    error_msg = f"签名失败，错误信息: {errors}"
                    logger.error(error_msg)
                    raise WebSocketError(error_msg)
                
                if data and len(data) >= 2:
                    sign = data[0]
                    cert_no = data[1]
                    return {
                        "sign": sign,
                        "cert_no": cert_no
                    }
                elif data and len(data) == 1:
                    sign = data[0]
                    return {
                        "sign": sign,
                        "cert_no": None
                    }
                else:
                    error_msg = "响应中未找到 Data 字段或 Data 为空"
                    raise WebSocketError(error_msg)
            else:
                error_msg = "无法识别的响应格式"
                logger.error(f"{error_msg}: {response}")
                raise WebSocketError(error_msg)
                
        except websockets.exceptions.ConnectionClosed as e:
            # 连接关闭，标记为不可用
            logger.warning(f"连接已关闭: {e}")
            self.connected = False
            self.websocket = None
            raise WebSocketError(f"WebSocket 连接已关闭: {e}")
        except websockets.exceptions.WebSocketException as e:
            error_msg = f"WebSocket 连接错误: {e}"
            logger.error(error_msg)
            self.connected = False
            self.websocket = None
            raise WebSocketError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"JSON 解析错误: {e}"
            logger.error(error_msg)
            raise WebSocketError(error_msg)
        except WebSocketError:
            raise
        except Exception as e:
            error_msg = f"获取签名失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.connected = False
            self.websocket = None
            raise WebSocketError(error_msg)

    def start(self):
        """启动方法（保持接口兼容，但不需要做任何事）"""
        logger.info("WebSocketWrapper 已准备就绪（使用连接复用模式）")
        pass

    def stop(self):
        """停止方法（关闭现有连接）"""
        if self.websocket:
            try:
                asyncio.run(self._close_connection())
            except Exception as e:
                logger.error(f"关闭连接时出错: {e}")
        logger.info("WebSocketWrapper 已停止")

    async def _close_connection(self):
        """关闭连接"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
            finally:
                self.websocket = None
                self.connected = False

    async def _get_sign_async(self, in_data: str, passwd: str) -> dict:
        """
        异步方法：获取签名（使用连接复用）
        
        Args:
            in_data: 待签名的数据字符串
            passwd: 密码
            
        Returns:
            dict: 包含 sign (签名) 和 cert_no (证书序列号) 的字典
            
        Raises:
            WebSocketError: 当 WebSocket 调用失败时
        """
        # 最多重试1次（失败时重新创建连接）
        max_retries = 1
        
        for retry in range(max_retries + 1):
            try:
                # 确保连接可用
                websocket = await self._ensure_connection()
                
                # 使用连接获取签名
                return await self._get_sign_with_connection(websocket, in_data, passwd)
                
            except WebSocketError as e:
                # 如果是连接错误且还有重试机会，清除连接状态后重试
                if "连接" in str(e) and retry < max_retries:
                    logger.debug(f"连接失败，重试 {retry + 1}/{max_retries + 1}")
                    self.connected = False
                    self.websocket = None
                    continue
                else:
                    raise
            except Exception as e:
                # 其他错误直接抛出
                raise WebSocketError(f"获取签名失败: {e}")

    def get_code(self, data: str, pwdstr: str) -> str:
        """
        等价于 Sign64Wrapper.get_code 的行为：
        
        - 通过 WebSocket 获取签名和证书序列号（使用连接复用）
        - 返回 "签名字符串||证书序列号"
        - 使用锁保护，确保同一时间只有一个请求在执行
        
        Args:
            data: 待签名的数据字符串
            pwdstr: 密码
            
        Returns:
            str: "签名字符串||证书序列号" 格式的字符串
            
        Raises:
            WebSocketError: 当 WebSocket 调用失败时
        """
        # 输入验证
        if not isinstance(data, str):
            raise WebSocketError("参数 'data' 必须是字符串类型")
        if not isinstance(pwdstr, str):
            raise WebSocketError("参数 'pwdstr' 必须是字符串类型")
        if not data:
            raise WebSocketError("参数 'data' 不能为空")
        if not pwdstr:
            raise WebSocketError("参数 'pwdstr' 不能为空")
        
        # 使用锁保护，确保同一时间只有一个请求在执行
        with self.lock:
            if not self.is_available():
                raise WebSocketError("WebSocket 服务未正确初始化")

            try:
                # 获取或创建事件循环
                loop = self._get_or_create_loop()
                
                # 运行异步函数（使用连接复用）
                result = loop.run_until_complete(self._get_sign_async(data, pwdstr))
                
                sign = result.get("sign")
                cert_no = result.get("cert_no")
                
                if not sign:
                    raise WebSocketError("签名结果为空")
                
                if not cert_no:
                    raise WebSocketError("证书序列号为空")
                
                # 返回与 Sign64Wrapper 相同的格式
                return f"{sign}||{cert_no}"
                
            except WebSocketError:
                raise
            except RuntimeError as e:
                # 处理事件循环冲突的情况
                if "运行中的事件循环" in str(e):
                    error_msg = "当前环境不支持同步调用异步函数，请使用异步接口"
                    logger.error(error_msg)
                    raise WebSocketError(error_msg)
                raise
            except Exception as e:
                error_msg = f"调用 WebSocket 签名服务失败: {e}"
                logger.error(error_msg, exc_info=True)
                raise WebSocketError(error_msg)


__all__ = ["WebSocketWrapper", "WebSocketError"]
