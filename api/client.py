"""
api/client.py - D2R 공포구역 API 클라이언트
지원 소스:
  - d2runewizard.com (헤더 토큰 방식)
  - d2emu.com        (Bearer 토큰 방식)
"""
from __future__ import annotations

import time
import requests
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────── 데이터 모델 ─────────────────────────────────

@dataclass
class TZInfo:
    """공포구역 정보 컨테이너."""
    current_zone: str = "불명"          # 현재 공포구역 (영문)
    next_zone: str = "불명"            # 다음 공포구역 (영문, 없으면 "불명")
    next_update_ts: float = 0.0        # 다음 갱신 Unix timestamp
    source: str = ""                    # 데이터 출처
    error: Optional[str] = None        # 오류 메시지

    def seconds_until_update(self) -> int:
        remaining = int(self.next_update_ts - time.time())
        return max(remaining, 0)


# ──────────────────────────── d2runewizard 클라이언트 ─────────────────────────

_D2RW_URL = "https://d2runewizard.com/api/terror-zone"
_D2RW_PLANNED_URL = "https://d2runewizard.com/api/terror-zone/planned"
_TIMEOUT = 10  # 초


def _fetch_d2runewizard(token: str) -> TZInfo:
    """d2runewizard.com에서 공포구역 정보를 가져옵니다."""
    headers = {
        "D2R-Contact-Token": token,
        "Accept": "application/json",
    }
    try:
        resp = requests.get(_D2RW_URL, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # 응답 구조 파싱 (실제 API 응답 형식에 맞게 처리)
        tz_data = data.get("terrorZone") or data
        current = _extract_zone_name(tz_data, "highestProbabilityZone", "zone", "current")
        next_zone = _extract_next_zone(tz_data)

        # 다음 정각까지 남은 시간 계산 (공포구역은 매 정각 갱신)
        next_ts = _next_hour_timestamp()

        return TZInfo(
            current_zone=current,
            next_zone=next_zone,
            next_update_ts=next_ts,
            source="d2runewizard",
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            return TZInfo(error="❌ 토큰이 유효하지 않습니다 (401 Unauthorized).\n설정에서 토큰을 확인해주세요.")
        return TZInfo(error=f"❌ API 오류: {e}")
    except requests.exceptions.ConnectionError:
        return TZInfo(error="⚠️ 네트워크 연결 실패.\n인터넷 연결을 확인해주세요.")
    except requests.exceptions.Timeout:
        return TZInfo(error="⚠️ 요청 시간 초과 (10초).")
    except Exception as e:
        return TZInfo(error=f"❌ 예기치 않은 오류: {e}")


# ───────────────────────────── d2emu 클라이언트 ───────────────────────────────

_D2EMU_URL = "https://d2emu.com/api/v1/tz"


def _fetch_d2emu(token: str) -> TZInfo:
    """d2emu.com에서 공포구역 정보를 가져옵니다."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(_D2EMU_URL, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        current = _extract_zone_name(data, "current_zone", "zone", "current")
        next_zone = _extract_zone_name(data, "next_zone", "next", "")
        if not next_zone:
            next_zone = "불명"

        next_ts = _next_hour_timestamp()
        return TZInfo(
            current_zone=current,
            next_zone=next_zone,
            next_update_ts=next_ts,
            source="d2emu",
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            return TZInfo(error="❌ 토큰이 유효하지 않습니다 (401 Unauthorized).\n설정에서 토큰을 확인해주세요.")
        return TZInfo(error=f"❌ API 오류: {e}")
    except requests.exceptions.ConnectionError:
        return TZInfo(error="⚠️ 네트워크 연결 실패.\n인터넷 연결을 확인해주세요.")
    except requests.exceptions.Timeout:
        return TZInfo(error="⚠️ 요청 시간 초과 (10초).")
    except Exception as e:
        return TZInfo(error=f"❌ 예기치 않은 오류: {e}")


# ────────────────────────────── 공개 인터페이스 ───────────────────────────────

def fetch_terror_zone(api_source: str, token: str) -> TZInfo:
    """
    설정된 소스로 공포구역 정보를 가져옵니다.

    Args:
        api_source: "d2runewizard" 또는 "d2emu"
        token: API 토큰

    Returns:
        TZInfo 객체
    """
    if not token:
        return TZInfo(error="⚠️ API 토큰이 설정되지 않았습니다.\n우클릭 → 설정에서 토큰을 입력해주세요.")

    if api_source == "d2emu":
        return _fetch_d2emu(token)
    else:
        return _fetch_d2runewizard(token)


# ────────────────────────────── 내부 헬퍼 ────────────────────────────────────

def _extract_zone_name(data: dict, *keys: str) -> str:
    """여러 키 이름을 시도하여 구역명을 추출합니다."""
    for key in keys:
        val = data.get(key)
        if isinstance(val, str) and val:
            return val
        if isinstance(val, dict):
            # 중첩 구조: {"zone": {"name": "..."}}
            name = val.get("name") or val.get("zone") or val.get("id") or ""
            if name:
                return str(name)
    return "불명"


def _extract_next_zone(data: dict) -> str:
    """d2runewizard 응답에서 다음 구역명을 추출."""
    # planned 필드 또는 nextZone 필드 탐색
    for key in ("nextZone", "next_zone", "planned", "plannedZone"):
        val = data.get(key)
        if isinstance(val, str) and val:
            return val
        if isinstance(val, dict):
            name = val.get("name") or val.get("zone") or ""
            if name:
                return str(name)
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, dict):
                name = first.get("name") or first.get("zone") or ""
                if name:
                    return str(name)
            elif isinstance(first, str):
                return first
    return "불명"


def _next_hour_timestamp() -> float:
    """다음 정각의 Unix timestamp를 반환합니다 (공포구역은 매 정각 갱신)."""
    now = time.time()
    # 다음 정각 = 현재 시각에서 초 단위를 올림하여 정각 계산
    return (int(now // 3600) + 1) * 3600
