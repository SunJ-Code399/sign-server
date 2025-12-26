"""
测试基于 Sign64.dll 的 HTTP POST 接口

依赖服务：
    python app.py

默认地址：
    http://localhost:8801/getCode

注意：请求和响应都使用 AES 加密
"""

import json

import requests
from aes_util import mysql_adapter_encrypt, mysql_adapter_decrypt
import config


def test_sign64_getcode():
    """测试 Sign64 getCode 接口（使用 AES 加密）"""
    url = "http://localhost:8801/getCode"

    # 测试数据（根据实际业务可调整）
    request_data = {
        "str": "test_data_string",
        "pwdstr": "00000000",
    }

    print("=" * 60)
    print("测试 HTTP POST /getCode 接口 (Sign64 Service)")
    print("=" * 60)
    print(f"请求 URL: {url}")
    print(f"请求数据（明文）: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    print()

    try:
        # 加密请求数据
        plaintext = json.dumps(request_data, ensure_ascii=False)
        cipher_text = mysql_adapter_encrypt(config.AES_KEY, plaintext, encoding="UTF-8")
        print(f"请求数据（密文）: {cipher_text[:100]}...")
        print()

        # 发送 POST 请求（请求体是密文）
        response = requests.post(url, data=cipher_text.encode('utf-8'))

        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print()

        result = response.json()
        print(f"响应数据（外层）: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print()

        # 处理成功情况（code=200）
        if result.get("code") == 200 and "data" in result:
            encrypted_data = result["data"]
            
            # 解密响应数据
            if isinstance(encrypted_data, str):
                print(f"响应 data（密文）: {encrypted_data[:100]}...")
                decrypted_data = mysql_adapter_decrypt(config.AES_KEY, encrypted_data, encoding="UTF-8")
                print(f"响应 data（解密后）: {decrypted_data}")
                print()
                
                # 解析解密后的 JSON
                data_obj = json.loads(decrypted_data)
                
                # 检查拆分后的格式（sign 和 certNo）
                if "sign" in data_obj and "certNo" in data_obj:
                    sign = data_obj["sign"]
                    cert_no = data_obj["certNo"]
                    print("结果（已拆分）:")
                    print(f"  sign: {sign}")
                    print(f"  certNo: {cert_no}")
                    print()
                    print("✓ Sign64 getCode 测试成功")
                    return True
                else:
                    print(f"✗ 响应数据格式不正确，缺少 sign 或 certNo: {data_obj}")
                    return False
            else:
                print(f"✗ 响应 data 不是字符串类型: {type(encrypted_data)}")
                return False
        
        # 处理错误情况（code=500，无法拆分）
        elif result.get("code") == 500:
            error_msg = result.get("msg", "")
            print(f"✗ 结果无法拆分，返回错误")
            print(f"错误信息（原始结果）: {error_msg}")
            print()
            
            # 检查原始结果格式
            if "||" in error_msg:
                parts = error_msg.split("||", 1)
                print("原始结果拆分:")
                for i, part in enumerate(parts, 1):
                    print(f"  部分 {i}: {part!r} (长度: {len(part)}, 是否为空: {not part.strip()})")
                print()
            
            print("✗ Sign64 getCode 测试失败：结果无法拆分")
            return False
        
        # 其他错误情况
        else:
            print(f"✗ 响应格式不正确: code={result.get('code')}, msg={result.get('msg')}")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ 连接失败，请确保服务已启动: python app.py")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON 解析失败: {e}")
        return False
    except Exception as e:  # pragma: no cover - 仅用于手动测试
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n请确保 Flask 服务已启动: python app.py")
    input("\n按回车键开始测试...\n")

    test_sign64_getcode()


