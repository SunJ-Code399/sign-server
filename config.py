# config.py
# Flask应用配置文件

# AES解密密钥
AES_KEY = "1234567887654321"

# XML文件存储目录
SAVE_FOLDER = "./xml_files/"

# Flask服务配置
HOST = "0.0.0.0"
PORT = 8801

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# WebSocket 签名服务配置
# WebSocket 接口来源于海关程序，需要先安装海关卡驱动并插入操作员卡
# 优先使用本地地址
WS_URL = "ws://127.0.0.1:61232"

