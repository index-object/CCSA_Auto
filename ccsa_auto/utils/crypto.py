"""外部平台(auth-v2)登录请求加密工具。

新版平台登录接口 ``auth-v2/pwdLogin`` 要求对请求体加密，规则与前端
``index-*.js`` 请求拦截器保持一致：

1. 每次请求随机生成 32 位字母数字组成的 AES 密钥；
2. 请求体 = ``Base64(AES-256-ECB/PKCS7(JSON 字符串))``；
3. 请求头 ``encrypt-key`` = ``Base64(RSA_PKCS1v15(Base64(AES 密钥)))``；
4. 请求头 ``isencrypt: true``。

对应前端实现（反混淆后）::

    aj = () => CryptoJS.enc.Utf8.parse(random32())
    lj = (e) => CryptoJS.enc.Base64.stringify(e)
    n4 = (e, t) => CryptoJS.AES.encrypt(e, t,
             {mode: ECB, padding: Pkcs7}).toString()
    Fj = (e) => new JSEncrypt().setPublicKey(publicKey).encrypt(e)
    headers["encrypt-key"] = Fj(lj(aesKey))
    data = n4(JSON.stringify(data), aesKey)
"""

import base64
import json
import secrets
import string

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# 前端硬编码的 RSA 公钥（SubjectPublicKeyInfo, DER -> Base64）
RSA_PUBLIC_KEY_B64 = (
    "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAKoR8mX0rGKLqzcWmOzbfj64K8ZIgOdH"
    "nzkXSOVOZbFu/TJhZ7rFAN+eaGkl3C4buccQd/EjEsj9ir7ijT7h96MCAwEAAQ=="
)

# 前端密钥字符集：A-Z a-z 0-9
_AES_KEY_ALPHABET = string.ascii_letters + string.digits

# AES 密钥长度（32 字符 -> 256 bit）
AES_KEY_LENGTH = 32

_BLOCK_SIZE = 16

_public_key = None


def _get_public_key():
    """懒加载并缓存 RSA 公钥对象。"""
    global _public_key
    if _public_key is None:
        der = base64.b64decode(RSA_PUBLIC_KEY_B64)
        _public_key = serialization.load_der_public_key(der)
    return _public_key


def generate_aes_key(length: int = AES_KEY_LENGTH) -> bytes:
    """生成随机的 AES 密钥（原始 ASCII 字节）。"""
    return "".join(
        secrets.choice(_AES_KEY_ALPHABET) for _ in range(length)
    ).encode("utf-8")


def _pkcs7_pad(data: bytes, block_size: int = _BLOCK_SIZE) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(data: bytes, block_size: int = _BLOCK_SIZE) -> bytes:
    if not data or len(data) % block_size != 0:
        raise ValueError("无效的密文长度")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size or data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("无效的 PKCS7 填充")
    return data[:-pad_len]


def aes_encrypt(plaintext: str, key: bytes) -> str:
    """AES-256-ECB/PKCS7 加密，返回 Base64 字符串。"""
    raw = plaintext.encode("utf-8")
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    ciphertext = encryptor.update(_pkcs7_pad(raw)) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")


def aes_decrypt(ciphertext_b64: str, key: bytes) -> str:
    """AES-256-ECB/PKCS7 解密 Base64 密文，返回明文字符串。"""
    ciphertext = base64.b64decode(ciphertext_b64)
    decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return _pkcs7_unpad(plaintext).decode("utf-8")


def rsa_encrypt(data: bytes) -> str:
    """使用平台公钥进行 RSA(PKCS#1 v1.5) 加密，返回 Base64 字符串。"""
    ciphertext = _get_public_key().encrypt(data, padding.PKCS1v15())
    return base64.b64encode(ciphertext).decode("ascii")


def encrypt_payload(payload) -> tuple[str, str]:
    """加密登录载荷。

    Args:
        payload: 待加密的数据，dict 会先序列化为 JSON 字符串。

    Returns:
        tuple: ``(请求体, encrypt-key 请求头)``
    """
    if not isinstance(payload, str):
        payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    aes_key = generate_aes_key()
    body = aes_encrypt(payload, aes_key)
    encrypt_key = rsa_encrypt(base64.b64encode(aes_key))
    return body, encrypt_key
