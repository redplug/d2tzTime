"""
config.py - 설정 저장/불러오기
config.json에 앱 설정을 저장합니다. 토큰은 base64+XOR 난독화처리.
"""
import json
import base64
import os
from pathlib import Path

# config.json 저장 위치: 실행 파일과 같은 폴더
CONFIG_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent / "config.json"

# XOR 키 (단순 난독화용)
_XOR_KEY = b"D2TZ_OVL_K3Y"

DEFAULT_CONFIG = {
    "api_source": "d2runewizard",   # "d2runewizard" | "d2emu"
    "token_d2rw": "",               # d2runewizard 토큰 (난독화 저장)
    "token_d2emu": "",              # d2emu 토큰 (난독화 저장)
    "x": 100,                       # 창 X 위치
    "y": 100,                       # 창 Y 위치
    "alpha": 0.85,                  # 투명도 (0.1 ~ 1.0)
    "always_on_top": True,          # 항상 위
    "lock_position": False,         # 위치 고정
    "language": "ko",               # "ko" | "en"
}


def _obfuscate(plain: str) -> str:
    """문자열을 XOR + base64로 난독화."""
    if not plain:
        return ""
    data = plain.encode("utf-8")
    key = _XOR_KEY
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(xored).decode("ascii")


def _deobfuscate(encoded: str) -> str:
    """난독화된 문자열을 복원."""
    if not encoded:
        return ""
    try:
        data = base64.b64decode(encoded.encode("ascii"))
        key = _XOR_KEY
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return xored.decode("utf-8")
    except Exception:
        return ""


def load_config() -> dict:
    """config.json을 불러옵니다. 없으면 DEFAULT_CONFIG 반환."""
    if not CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        # 기본값과 병합 (새 키가 생겼을 때 대비)
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(raw)
        # 토큰 복호화
        cfg["token_d2rw"] = _deobfuscate(cfg.get("token_d2rw", ""))
        cfg["token_d2emu"] = _deobfuscate(cfg.get("token_d2emu", ""))
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """설정을 config.json에 저장합니다. 토큰은 난독화하여 저장."""
    to_save = dict(cfg)
    to_save["token_d2rw"] = _obfuscate(cfg.get("token_d2rw", ""))
    to_save["token_d2emu"] = _obfuscate(cfg.get("token_d2emu", ""))
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)
