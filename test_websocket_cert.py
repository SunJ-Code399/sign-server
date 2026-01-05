# -*- coding: utf-8 -*-
"""
通过 WebSocket 获取证书序列号和签名的测试脚本
"""
import asyncio
import json
import logging
import websockets

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket 服务器地址
WS_URL = "wss://wss.singlewindow.cn:61231/"


async def _handle_handshake(websocket):
    """
    处理 WebSocket 握手消息
    """
    handshake_json = await websocket.recv()
    logger.info(f"收到握手消息: {handshake_json}")
    
    # 解析握手消息
    handshake = json.loads(handshake_json)
    method = handshake.get("_method")
    if method == "open":
        logger.info("握手成功")
        return True
    else:
        logger.warning(f"收到非预期的握手消息，方法: {method}")
        return False


async def get_cert_no():
    """
    通过 WebSocket 获取证书序列号
    """
    try:
        logger.info(f"正在连接 WebSocket 服务器: {WS_URL}")
        
        # 创建 WebSocket 连接（SSL 验证可能需要根据实际情况调整）
        async with websockets.connect(
            WS_URL,
            ssl=True  # WSS 需要 SSL
        ) as websocket:
            logger.info("WebSocket 连接成功")
            
            # 先接收握手消息（open 方法的响应）
            await _handle_handshake(websocket)
            
            # 构建获取证书序列号的请求报文
            request = {
                "_method": "cus-sec_SpcGetCertNo",
                "_id": 2,
                "args": {}
            }
            request_json = json.dumps(request)
            
            logger.info(f"发送请求: {request_json}")
            
            # 发送请求
            await websocket.send(request_json)
            
            # 接收证书序列号响应
            response_json = await websocket.recv()
            logger.info(f"收到响应: {response_json}")
            
            # 解析响应
            response = json.loads(response_json)
            
            # 检查响应状态
            status = response.get("_status")
            if status != "00":
                logger.error(f"响应状态错误: {status}")
                logger.error(f"完整响应: {response}")
                return None
            
            # 检查响应方法
            response_method = response.get("_method")
            if response_method != "cus-sec_SpcGetCertNo":
                logger.error(f"响应方法不匹配，期望: cus-sec_SpcGetCertNo，实际: {response_method}")
                logger.error(f"完整响应: {response}")
                return None
            
            # 提取证书序列号
            args = response.get("_args", {})
            data = args.get("Data", [])
            
            if data and len(data) > 0:
                cert_no = data[0]
                logger.info(f"证书序列号: {cert_no}")
                return cert_no
            else:
                logger.error("响应中未找到 Data 字段或 Data 为空")
                logger.error(f"完整响应: {response}")
                return None
                
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket 连接错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        return None
    except Exception as e:
        logger.error(f"获取证书序列号失败: {e}", exc_info=True)
        return None


async def get_sign(in_data, passwd):
    """
    通过 WebSocket 获取签名
    
    Args:
        in_data: 待签名的数据字符串
        passwd: 密码
    
    Returns:
        dict: 包含 sign (签名) 和 cert_no (证书序列号) 的字典，失败返回 None
        响应格式: Data[0] 是签名字符串, Data[1] 是证书序列号
    """
    try:
        logger.info(f"正在连接 WebSocket 服务器: {WS_URL}")
        
        # 创建 WebSocket 连接
        async with websockets.connect(
            WS_URL,
            ssl=True  # WSS 需要 SSL
        ) as websocket:
            logger.info("WebSocket 连接成功")
            
            # 先接收握手消息
            await _handle_handshake(websocket)
            
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
            
            logger.info(f"发送签名请求: {request_json}")
            
            # 发送请求
            await websocket.send(request_json)
            
            # 接收签名响应
            response_json = await websocket.recv()
            logger.info(f"收到响应: {response_json}")
            
            # 解析响应
            response = json.loads(response_json)
            
            # 检查响应格式（可能是直接返回 Result/Data/Error，也可能在 _args 中）
            if "Result" in response:
                # 直接格式：{"Result":true,"Data":["签名","证书序列号"],"Error":[]}
                result = response.get("Result")
                data = response.get("Data", [])
                errors = response.get("Error", [])
            elif "_args" in response:
                # 嵌套格式：{"_id":1,"_method":"...","_status":"00","_args":{"Result":true,"Data":["签名","证书序列号"],"Error":[]}}
                args = response.get("_args", {})
                result = args.get("Result")
                data = args.get("Data", [])
                errors = args.get("Error", [])
                status = response.get("_status")
                if status and status != "00":
                    logger.error(f"响应状态错误: {status}")
                    logger.error(f"完整响应: {response}")
                    return None
            else:
                logger.error("无法识别的响应格式")
                logger.error(f"完整响应: {response}")
                return None
            
            if not result:
                logger.error(f"签名失败，错误信息: {errors}")
                logger.error(f"完整响应: {response}")
                return None
            
            if data and len(data) >= 2:
                sign = data[0]  # 签名字符串
                cert_no = data[1]  # 证书序列号
                logger.info(f"签名成功，签名长度: {len(sign)}, 证书序列号: {cert_no}")
                return {
                    "sign": sign,
                    "cert_no": cert_no
                }
            elif data and len(data) == 1:
                # 只有签名，没有证书序列号
                sign = data[0]
                logger.info(f"签名成功（无证书序列号），签名长度: {len(sign)}")
                return {
                    "sign": sign,
                    "cert_no": None
                }
            else:
                logger.error("响应中未找到 Data 字段或 Data 为空")
                logger.error(f"完整响应: {response}")
                return None
                
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket 连接错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        return None
    except Exception as e:
        logger.error(f"获取签名失败: {e}", exc_info=True)
        return None


def main():
    """
    主函数 - 测试获取证书序列号和签名
    """
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "sign":
        # 测试签名功能
        logger.info("=" * 50)
        logger.info("开始测试 WebSocket 获取签名")
        logger.info("=" * 50)
        
        # 可以从命令行参数获取，或使用默认值
        in_data = sys.argv[2] if len(sys.argv) > 2 else "test_data_string"
        passwd = sys.argv[3] if len(sys.argv) > 3 else "Vitup124"
        
        result = asyncio.run(get_sign(in_data, passwd))
        
        if result:
            logger.info("=" * 50)
            logger.info(f"成功获取签名")
            logger.info(f"签名: {result['sign']}")
            if result['cert_no']:
                logger.info(f"证书序列号: {result['cert_no']}")
            logger.info("=" * 50)
            return result
        else:
            logger.error("=" * 50)
            logger.error("获取签名失败")
            logger.error("=" * 50)
            return None
    else:
        # 默认测试证书序列号功能
        logger.info("=" * 50)
        logger.info("开始测试 WebSocket 获取证书序列号")
        logger.info("=" * 50)
        logger.info("提示: 使用 'py test_websocket_cert.py sign [数据] [密码]' 测试签名功能")
        logger.info("=" * 50)
        
        cert_no = asyncio.run(get_cert_no())
        
        if cert_no:
            logger.info("=" * 50)
            logger.info(f"成功获取证书序列号: {cert_no}")
            logger.info("=" * 50)
            return cert_no
        else:
            logger.error("=" * 50)
            logger.error("获取证书序列号失败")
            logger.error("=" * 50)
            return None


if __name__ == "__main__":
    main()
