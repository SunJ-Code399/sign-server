"""
Sign64.dll 封装

根据从 ILSpy 反编译得到的 C# 代码：

    [DllImport("Sign64.dll")]
    private static extern uint GetCardID(byte[] szCardID, uint[] nCardIDLen);

    [DllImport("Sign64.dll")]
    private static extern uint GetCertNo(byte[] szCertNo, uint[] nCertNoLen);

    [DllImport("Sign64.dll", CharSet = CharSet.Ansi)]
    public static extern uint Sign(byte[] src, uint srcLen,
                                   byte[] sign1, uint[] signLen, char[] pwd);

这里使用 ctypes 封装这些函数，并提供一个高层的 get_code(str, pwdstr)
方法，其行为与 C# WebService1.getCode 基本一致：

    - 使用 UTF-8 将 str 编码为字节
    - 使用固定长度 172 字节的缓冲区接收签名
    - 调用 Sign 和 GetCertNo
    - 返回 \"签名字符串||证书号字符串\"
"""

import ctypes
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Sign64Error(RuntimeError):
    """Sign64 相关错误"""


class Sign64Wrapper:
    """Sign64.dll 的 Python 封装"""

    def __init__(self, dll_path: Optional[str] = None) -> None:
        # 仅在 Windows 上尝试加载
        if sys.platform != "win32":
            logger.warning(
                "当前平台不是 Windows (sys.platform=%s)，无法直接加载 Sign64.dll",
                sys.platform,
            )
            self.dll = None
            return

        if dll_path is None:
            dll_path = self._find_dll_path()

        if not dll_path or not Path(dll_path).exists():
            logger.error("未找到 Sign64.dll，搜索路径失败")
            self.dll = None
            return

        try:
            # DllImport 默认使用 WinAPI (stdcall)，ctypes 中对应 WinDLL
            self.dll = ctypes.WinDLL(dll_path)
            logger.info("成功加载 Sign64.dll: %s", dll_path)
        except Exception as exc:  # pragma: no cover - 平台相关
            logger.error("加载 Sign64.dll 失败: %s", exc)
            self.dll = None
            return

        # 配置函数签名
        self._setup_functions()

    @staticmethod
    def _find_dll_path() -> Optional[str]:
        """
        在常见位置查找 Sign64.dll：
        - <project_root>/dll/Sign64.dll
        """
        base_dir = Path(__file__).resolve().parent  # 项目根目录
        candidates = [
            base_dir / "dll" / "Sign64.dll",
        ]

        for p in candidates:
            if p.exists():
                return str(p)
        return None

    def _setup_functions(self) -> None:
        """根据 C# DllImport 声明配置函数签名"""
        # uint GetCertNo(byte[] szCertNo, uint[] nCertNoLen);
        try:
            self.GetCertNo = self.dll.GetCertNo
            self.GetCertNo.argtypes = [
                ctypes.c_char_p,                  # szCertNo (输出缓冲区)
                ctypes.POINTER(ctypes.c_uint32),  # nCertNoLen[0]
            ]
            self.GetCertNo.restype = ctypes.c_uint32
        except AttributeError as exc:
            logger.error("Sign64.dll 中未找到 GetCertNo: %s", exc)
            self.GetCertNo = None  # type: ignore[assignment]

        # uint GetCardID(byte[] szCardID, uint[] nCardIDLen);
        try:
            self.GetCardID = self.dll.GetCardID
            self.GetCardID.argtypes = [
                ctypes.c_char_p,                  # szCardID (输出缓冲区)
                ctypes.POINTER(ctypes.c_uint32),  # nCardIDLen[0]
            ]
            self.GetCardID.restype = ctypes.c_uint32
        except AttributeError:
            # 有些场景可能并不导出 GetCardID，非致命
            logger.info("Sign64.dll 中未找到 GetCardID (可忽略)")
            self.GetCardID = None  # type: ignore[assignment]

        # uint Sign(byte[] src, uint srcLen, byte[] sign1, uint[] signLen, char[] pwd);
        try:
            self.Sign = self.dll.Sign
            self.Sign.argtypes = [
                ctypes.c_char_p,                  # src
                ctypes.c_uint32,                  # srcLen
                ctypes.c_char_p,                  # sign1 (输出缓冲区)
                ctypes.POINTER(ctypes.c_uint32),  # signLen[0]
                ctypes.c_char_p,                  # pwd (按 CharSet.Ansi 处理为字节串)
            ]
            self.Sign.restype = ctypes.c_uint32
        except AttributeError as exc:
            logger.error("Sign64.dll 中未找到 Sign 函数: %s", exc)
            self.Sign = None  # type: ignore[assignment]

    # 高层封装 -----------------------------------------------------------------

    def is_available(self) -> bool:
        """检查 DLL 是否加载成功且关键函数可用"""
        return (
            self.dll is not None
            and getattr(self, "Sign", None) is not None
            and getattr(self, "GetCertNo", None) is not None
        )

    def get_code(self, data: str, pwdstr: str) -> str:
        """
        等价于 C# WebService1.getCode(string str, string pwdstr) 的行为：

        - 对 data 做签名，得到 sign 字节
        - 读取证书号 cert
        - 返回 \"sign||cert\"
        """
        if not self.is_available():
            raise Sign64Error("Sign64.dll 未正确初始化或缺少必要函数")

        # 1. 源数据 UTF-8 编码
        src_bytes = data.encode("utf-8")
        src_len = ctypes.c_uint32(len(src_bytes))

        # 2. 签名缓冲区，长度与 C# 中的 172 一致
        sign_buf_len = ctypes.c_uint32(172)
        sign_buf = ctypes.create_string_buffer(sign_buf_len.value)

        # 3. 密码（C# CharSet.Ansi + char[]，这里按 ANSI 字节串处理）
        pwd_bytes = pwdstr.encode("ascii", errors="ignore") or b""
        pwd_c = ctypes.c_char_p(pwd_bytes)

        # 4. 调用 Sign
        res = self.Sign(
            src_bytes,         # src
            src_len,           # srcLen
            sign_buf,          # sign1
            ctypes.byref(sign_buf_len),  # signLen[0]
            pwd_c,             # pwd
        )

        if res != 0:
            raise Sign64Error(f"Sign 调用失败，错误码: {res}")

        # 5. 准备证书号缓冲区（C# 中使用 8 字节数组）
        cert_buf_len = ctypes.c_uint32(8)
        cert_buf = ctypes.create_string_buffer(cert_buf_len.value)

        res2 = self.GetCertNo(
            cert_buf,
            ctypes.byref(cert_buf_len),
        )
        if res2 != 0:
            raise Sign64Error(f"GetCertNo 调用失败，错误码: {res2}")

        # 6. 按长度截断并解码（避免尾部填充的 0 字节干扰）
        sign_str = sign_buf.raw[: sign_buf_len.value].decode(
            "utf-8", errors="ignore"
        )
        cert_str = cert_buf.raw[: cert_buf_len.value].decode(
            "utf-8", errors="ignore"
        )

        return f"{sign_str}||{cert_str}"


__all__ = ["Sign64Wrapper", "Sign64Error"]


