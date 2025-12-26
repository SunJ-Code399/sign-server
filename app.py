"""
Flask Web应用主文件
提供/receive-xml接口，接收AES密文，解密为JSON后写入XML
同时提供基于 Sign64.dll 的 getCode 接口
"""
import logging
from flask import Flask, request, jsonify
import config
from services.xml_service import (
    decrypt_request_body,
    extract_directory,
    validate_request_data,
    save_xml_file,
    list_xml_files,
    delete_xml_file,
    encrypt_response_data,
    ensure_directory_exists,
)
from sign64_wrapper import Sign64Wrapper, Sign64Error

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# 返回JSON时禁用ASCII转义，保证中文直出
app.config["JSON_AS_ASCII"] = False
# 兼容Flask新版 JSON provider 的设置
try:
    app.json.ensure_ascii = False  # type: ignore
except Exception:
    pass

# 初始化 Sign64 封装
sign64 = Sign64Wrapper()


@app.route('/xml-files/list', methods=['POST'])
def list_files():
    """
    获取指定目录下的所有XML文件（文件名 + 内容）
    请求体：密文 -> 解密后JSON，可包含字段 目录
    返回：data 为对象时加密后返回
    """
    try:
        raw_body = request.get_data()
        logger.info("收到 xml-files/list 请求")
        request_data = decrypt_request_body(raw_body, config.AES_KEY, encoding="UTF-8")
        directory = extract_directory(request_data, config.SAVE_FOLDER)

        files = list_xml_files(directory)
        logger.info("xml-files/list 查询成功，文件数量=%d", len(files))
        resp_data = encrypt_response_data(files, config.AES_KEY)

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": resp_data
        }), 200
    except Exception as e:
        logger.error(f"查询XML文件列表失败: {e}", exc_info=True)
        return jsonify({
            "code": 500,
            "msg": f"查询失败: {str(e)}",
            "data": False
        }), 500


@app.route('/xml-files/add', methods=['POST'])
def add_file():
    """
    新增XML文件
    请求体：密文 -> 解密后JSON，需要 文件名、xml报文，可选 目录
    """
    try:
        raw_body = request.get_data()
        logger.info("收到 xml-files/add 请求")
        request_data = decrypt_request_body(raw_body, config.AES_KEY, encoding="UTF-8")

        try:
            filename, xml_content = validate_request_data(request_data)
            directory = extract_directory(request_data, config.SAVE_FOLDER)
        except ValueError as e:
            return jsonify({
                "code": 500,
                "msg": str(e),
                "data": False
            }), 400

        try:
            save_xml_file(filename, xml_content, directory)
        except Exception as e:
            return jsonify({
                "code": 500,
                "msg": str(e),
                "data": False
            }), 500

        return jsonify({
            "code": 200,
            "msg": "新增成功",
            "data": True
        }), 200
    except Exception as e:
        logger.error(f"新增XML文件失败: {e}", exc_info=True)
        return jsonify({
            "code": 500,
            "msg": f"服务器内部错误: {str(e)}",
            "data": False
        }), 500


@app.route('/xml-files/delete', methods=['POST'])
def delete_file():
    """
    删除指定XML文件
    请求体：密文 -> 解密后JSON，需要 文件名，可选 目录
    """
    try:
        raw_body = request.get_data()
        logger.info("收到 xml-files/delete 请求")
        request_data = decrypt_request_body(raw_body, config.AES_KEY, encoding="UTF-8")

        if not isinstance(request_data, dict):
            return jsonify({
                "code": 500,
                "msg": "请求数据必须是JSON对象",
                "data": False
            }), 400

        filename = request_data.get("filename")
        if not filename or not isinstance(filename, str):
            return jsonify({
                "code": 500,
                "msg": "filename不能为空且必须是字符串",
                "data": False
            }), 400

        directory = extract_directory(request_data, config.SAVE_FOLDER)

        try:
            delete_xml_file(filename, directory)
        except FileNotFoundError as e:
            return jsonify({
                "code": 500,
                "msg": str(e),
                "data": False
            }), 404
        except Exception as e:
            return jsonify({
                "code": 500,
                "msg": str(e),
                "data": False
            }), 500

        return jsonify({
            "code": 200,
            "msg": "删除成功",
            "data": True
        }), 200
    except Exception as e:
        logger.error(f"删除XML文件失败: {e}", exc_info=True)
        return jsonify({
            "code": 500,
            "msg": f"服务器内部错误: {str(e)}",
            "data": False
        }), 500


@app.route('/', methods=['GET'])
def root():
    """
    根路径，返回服务信息
    """
    return jsonify({
        "service": "Sign Server",
        "version": "1.0.0",
        "status": "running" if sign64.is_available() else "sign64_not_available",
        "endpoints": {
            "xml_files": {
                "list": {"method": "POST", "path": "/xml-files/list"},
                "add": {"method": "POST", "path": "/xml-files/add"},
                "delete": {"method": "POST", "path": "/xml-files/delete"},
            },
            "sign64": {
                "getCode": {"method": "POST", "path": "/getCode"},
            },
            "health": {"method": "GET", "path": "/health"},
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    sign64_status = "healthy" if sign64.is_available() else "sign64_not_available"
    return jsonify({
        "code": 200,
        "msg": "服务运行正常",
        "data": True,
        "sign64_status": sign64_status
    }), 200


@app.route('/getCode', methods=['POST'])
def getcode():
    """
    基于 Sign64.dll 的 getCode 接口
    
    请求体：密文 -> 解密后JSON，需要字段：
    {
        "str": "数据字符串",
        "pwdstr": "密码字符串"
    }
    
    响应：data 为对象时加密后返回
    {
        "code": 200,
        "msg": "成功",
        "data": "加密后的密文（包含 getCodeResult）"
    }
    """
    if not sign64.is_available():
        msg = "Sign64.dll 未正确加载，请确认运行环境为 Windows 且 DLL 路径正确"
        logger.error(msg)
        return jsonify({
            "code": 500,
            "msg": msg,
            "data": False
        }), 500
    
    try:
        # 获取并解密请求数据（与 XML 接口保持一致）
        raw_body = request.get_data()
        logger.info("收到 getCode 请求")
        request_data = decrypt_request_body(raw_body, config.AES_KEY, encoding="UTF-8")
        if not isinstance(request_data, dict):
            return jsonify({
                "code": 400,
                "msg": "请求数据必须是JSON对象",
                "data": False
            }), 400
        
        str_data = request_data.get("str")
        pwdstr = request_data.get("pwdstr")
        
        if str_data is None or pwdstr is None:
            return jsonify({
                "code": 400,
                "msg": "请求体必须包含 'str' 和 'pwdstr' 字段",
                "data": False
            }), 400
        
        if not isinstance(str_data, str) or not isinstance(pwdstr, str):
            return jsonify({
                "code": 400,
                "msg": "'str' 和 'pwdstr' 必须是字符串类型",
                "data": False
            }), 400

        
        result = sign64.get_code(str_data, pwdstr)
        
        logger.info("Sign64.getCode 调用成功，结果长度=%d", len(result))
        logger.debug("Sign64.getCode 返回结果: %r", result[:200])
        
        # 拆分结果：如果符合 "签名字符串||证书号字符串" 格式，且两部分都有值，则拆分
        # 如果无法拆分，返回错误并将结果放到msg中
        if "||" in result:
            parts = result.split("||", 1)  # 只分割一次，防止证书号中包含 ||
            if len(parts) == 2:
                sign = parts[0].strip()
                cert_no = parts[1].strip()
                # 检查两部分是否都有值
                if sign and cert_no:
                    response_data = {
                        "sign": sign,
                        "certNo": cert_no
                    }
                    logger.info("结果已拆分为 sign 和 certNo")
                    
                    # 加密响应数据（与 XML 接口保持一致）
                    resp_data = encrypt_response_data(response_data, config.AES_KEY)
                    
                    return jsonify({
                        "code": 200,
                        "msg": "成功",
                        "data": resp_data
                    }), 200
                else:
                    # 如果拆分后有空值，返回错误
                    logger.error("结果拆分后存在空值: sign=%r, certNo=%r", sign, cert_no)
                    return jsonify({
                        "code": 500,
                        "msg": result,
                        "data": False
                    }), 500
            else:
                # 如果拆分失败，返回错误
                logger.error("结果格式不符合预期，拆分后部分数量=%d", len(parts))
                return jsonify({
                    "code": 500,
                    "msg": result,
                    "data": False
                }), 500
        else:
            # 如果不包含 ||，返回错误
            logger.error("结果不包含分隔符 ||，无法拆分")
            return jsonify({
                "code": 500,
                "msg": result,
                "data": False
            }), 500
        
    except ValueError as e:
        # 解密失败或数据格式错误
        logger.error(f"请求数据解析失败: {e}", exc_info=True)
        return jsonify({
            "code": 400,
            "msg": str(e),
            "data": False
        }), 400
    except Sign64Error as e:
        logger.error("Sign64Error: %s", e, exc_info=True)
        return jsonify({
            "code": 500,
            "msg": str(e),
            "data": False
        }), 500
    except Exception as e:
        msg = f"调用 Sign64.getCode 失败: {e}"
        logger.error(msg, exc_info=True)
        return jsonify({
            "code": 500,
            "msg": msg,
            "data": False
        }), 500


if __name__ == '__main__':
    # 确保保存目录存在
    ensure_directory_exists(config.SAVE_FOLDER)
    
    logger.info("Flask应用启动")
    logger.info(f"AES密钥配置: {'已配置' if config.AES_KEY else '未配置'}")
    # logger.info(f"XML文件保存目录: {config.SAVE_FOLDER}")
    logger.info(f"服务地址: http://{config.HOST}:{config.PORT}")
    
    app.run(host=config.HOST, port=config.PORT, debug=True)

