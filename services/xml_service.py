import os
import json
import logging
from aes_util import mysql_adapter_decrypt, mysql_adapter_encrypt

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory_path: str):
    """确保目录存在"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info("创建目录: %s", directory_path)


def extract_directory(data: dict, default_dir: str) -> str:
    """从请求数据中提取目录"""
    directory = data.get("directory") if isinstance(data, dict) else None
    if directory and not isinstance(directory, str):
        raise ValueError("目录必须是字符串")
    return directory or default_dir


def validate_request_data(data: dict) -> tuple[str, str]:
    """校验并提取 filename 与 xml"""
    if not isinstance(data, dict):
        raise ValueError("请求数据必须是JSON对象")
    if "filename" not in data:
        raise ValueError("缺少必需字段: filename")
    if "xml" not in data:
        raise ValueError("缺少必需字段: xml")

    filename = data["filename"]
    xml_content = data["xml"]
    if not filename or not isinstance(filename, str):
        raise ValueError("filename不能为空且必须是字符串")
    if not xml_content or not isinstance(xml_content, str):
        raise ValueError("xml不能为空且必须是字符串")
    return filename, xml_content


def save_xml_file(filename: str, content: str, save_folder: str) -> str:
    """保存XML文件"""
    ensure_directory_exists(save_folder)
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".xml"):
        safe_filename += ".xml"
    file_path = os.path.join(save_folder, safe_filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("成功保存XML文件: %s", file_path)
        return file_path
    except OSError as e:
        logger.error("保存XML文件失败: %s", e, exc_info=True)
        raise IOError(f"文件写入失败: {e}")


def list_xml_files(save_folder: str) -> list:
    """列出目录下的XML文件及内容"""
    ensure_directory_exists(save_folder)
    results = []
    for name in sorted(os.listdir(save_folder)):
        if not name.lower().endswith(".xml"):
            continue
        file_path = os.path.join(save_folder, name)
        if not os.path.isfile(file_path):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            results.append({"filename": name, "xml": content})
        except Exception as e:
            logger.error("读取XML文件失败: %s - %s", file_path, e, exc_info=True)
            raise IOError(f"读取文件失败: {name}")
    return results


def delete_xml_file(filename: str, save_folder: str):
    """删除指定XML文件"""
    ensure_directory_exists(save_folder)
    safe_name = os.path.basename(filename)
    if not safe_name.lower().endswith(".xml"):
        safe_name += ".xml"
    file_path = os.path.join(save_folder, safe_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {safe_name}")
    try:
        os.remove(file_path)
        logger.info("删除XML文件成功: %s", file_path)
    except Exception as e:
        logger.error("删除XML文件失败: %s - %s", file_path, e, exc_info=True)
        raise IOError(f"删除文件失败: {safe_name}")


def decrypt_request_body(raw_body: bytes, key: str, encoding: str = "UTF-8") -> dict:
    """将密文请求体解密并解析为JSON"""
    if not raw_body:
        raise ValueError("请求体不能为空")
    cipher_text = raw_body.decode(encoding).strip()
    # 记录解密前的密文（只记录前200个字符，避免日志过长）
    logger.info("收到密文（解密前），长度=%d，内容预览: %s", len(cipher_text), cipher_text[:200])
    plain_text = mysql_adapter_decrypt(key, cipher_text, encoding=encoding)
    if plain_text is None:
        raise ValueError("解密结果为空")
    # 记录解密后的明文
    logger.info("解密成功（解密后），长度=%d，内容: %s", len(plain_text), plain_text)
    try:
        return json.loads(plain_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"解密后内容不是有效的JSON: {e}")


def encrypt_response_data(data_obj, key: str) -> str:
    """若data是对象/数组，则加密为密文返回；否则原样"""
    if isinstance(data_obj, (dict, list)):
        plaintext = json.dumps(data_obj, ensure_ascii=False)
        # 记录加密前的明文
        logger.info("准备加密响应数据（加密前），长度=%d，内容: %s", len(plaintext), plaintext[:500])
        cipher_text = mysql_adapter_encrypt(key, plaintext, encoding="UTF-8")
        # 记录加密后的密文（只记录前200个字符，避免日志过长）
        logger.info("加密成功（加密后），长度=%d，内容预览: %s", len(cipher_text), cipher_text[:200])
        return cipher_text
    return data_obj

