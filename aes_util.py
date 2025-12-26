"""
AES解密工具模块
实现与Java AESUtil.mysqlAdapterDecrypt方法兼容的AES解密功能
"""
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Util.Padding import pad
import binascii

logger = logging.getLogger(__name__)


def generate_mysql_aes_key(key: str, encoding: str = "UTF-8") -> bytes:
    """
    生成MySQL AES密钥
    与Java的generateMySQLAESKey方法兼容
    
    Args:
        key: 原始密钥字符串
        encoding: 字符编码，默认为UTF-8
        
    Returns:
        16字节的密钥字节数组
    """
    if not key:
        raise ValueError("加密Key配置异常")
    
    logger.debug(f"加密KEY: {key}")
    
    # 创建16字节的finalKey数组，初始化为0
    final_key = bytearray(16)
    
    # 将key的字节循环XOR到finalKey中
    key_bytes = key.encode(encoding)
    for i, b in enumerate(key_bytes):
        final_key[i % 16] ^= b
    
    return bytes(final_key)


def mysql_adapter_decrypt(key: str, ciphertext: str, encoding: str = "UTF-8") -> str:
    """
    MySQL适配器解密方法
    与Java的mysqlAdapterDecrypt方法兼容
    
    Args:
        key: AES解密密钥
        ciphertext: 十六进制编码的密文字符串
        encoding: 字符编码，默认为UTF-8
        
    Returns:
        解密后的明文字符串
        
    Raises:
        ValueError: 当密钥或密文为空时
        Exception: 解密失败时
    """
    if ciphertext is None:
        return None
    
    logger.debug(f"解密前 <{ciphertext}>")
    
    try:
        # 生成MySQL AES密钥
        secret_key = generate_mysql_aes_key(key, encoding)
        
        # 创建AES解密器（ECB模式，PKCS5填充）
        cipher = AES.new(secret_key, AES.MODE_ECB)
        
        # 将十六进制字符串解码为字节数组
        ciphertext_bytes = binascii.unhexlify(ciphertext)
        
        # 执行解密
        decrypted_bytes = cipher.decrypt(ciphertext_bytes)
        
        # 去除PKCS5填充
        decrypted_bytes = unpad(decrypted_bytes, AES.block_size)
        
        # 转换为UTF-8字符串
        result = decrypted_bytes.decode(encoding)
        
        logger.debug(f"解密后 <{result}>")
        return result
        
    except Exception as e:
        logger.error(f"解密失败: {e}", exc_info=True)
        raise Exception(f"解密失败: {str(e)}")


def mysql_adapter_encrypt(key: str, plaintext: str, encoding: str = "UTF-8") -> str:
    """
    MySQL适配器加密方法（输出十六进制字符串，与Java mysqlAdapterEncrypt兼容）
    """
    if plaintext is None:
        return None

    try:
        secret_key = generate_mysql_aes_key(key, encoding)
        cipher = AES.new(secret_key, AES.MODE_ECB)
        padded = pad(plaintext.encode(encoding), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return binascii.hexlify(encrypted).decode("ascii").upper()
    except Exception as e:
        logger.error(f"加密失败: {e}", exc_info=True)
        raise Exception(f"加密失败: {str(e)}")

