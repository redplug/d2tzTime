"""
api/client.py - D2R 공포구역 API 클라이언트
소스: d2tz.info (쿼리 파라미터 토큰 방식)
"""
from __future__ import annotations

import time
import requests
from dataclasses import dataclass
from typing import Optional


# ──────────────────────────────────── 데이터 모델 ────────────────────────────

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


_TIMEOUT = 10  # 초


# ──────────────────────────────── d2tz.info 클라이언트 ────────────────────────
# API 문서: https://www.d2tz.info/api
# 엔드포인트: GET https://api.d2tz.info/public/tz?token=YOUR_TOKEN
# 인증: 쿼리 파라미터 token= 또는 Authorization 헤더
# 응답: [{"time": 1710..., "end_time": 1710..., "zone_name": ["Dark Wood", ...], ...}]

_D2TZ_URL = "https://api.d2tz.info/public/tz"


def _fetch_d2tz(token: str) -> TZInfo:
    """d2tz.info에서 공포구역 정보를 가져옵니다."""
    now = int(time.time())

    try:
        resp = requests.get(
            _D2TZ_URL,
            params={"token": token},
            headers={"Authorization": token},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        current_zone = "불명"
        next_zone = "불명"
        update_ts = _next_hour_timestamp()

        if isinstance(data, list) and data:
            current_entry = None
            next_entry = None
            for entry in data:
                t_start = entry.get("time", 0)
                t_end = entry.get("end_time", 0)
                if t_start <= now <= t_end:
                    current_entry = entry
                    update_ts = float(t_end)
                elif t_start > now and next_entry is None:
                    next_entry = entry

            if current_entry is None and data:
                current_entry = data[0]
                if len(data) > 1:
                    next_entry = data[1]

            if current_entry:
                zones = current_entry.get("zone_name", [])
                if isinstance(zones, list) and zones:
                    current_zone = zones[0]
                elif isinstance(zones, str):
                    current_zone = zones

            if next_entry:
                zones = next_entry.get("zone_name", [])
                if isinstance(zones, list) and zones:
                    next_zone = zones[0]
                elif isinstance(zones, str):
                    next_zone = zones

        elif isinstance(data, dict):
            zones = data.get("zone_name", [])
            if isinstance(zones, list) and zones:
                current_zone = zones[0]
            elif isinstance(zones, str):
                current_zone = zones
            update_ts = float(data.get("end_time", _next_hour_timestamp()))

        return TZInfo(
            current_zone=current_zone,
            next_zone=next_zone,
            next_update_ts=update_ts,
            source="d2tz",
        )

    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 401:
                return TZInfo(error="❌ 토큰이 유효하지 않습니다 (401).\n설정에서 토큰을 확인해주세요.")
            if e.response.status_code == 403:
                return TZInfo(error="❌ 접근 거부 (403).\nd2tz.info/api 에서 토큰을 신청해주세요.")
        return TZInfo(error=f"❌ API 오류: {e}")
    except requests.exceptions.ConnectionError:
        return TZInfo(error="⚠️ 네트워크 연결 실패.\n인터넷 연결을 확인해주세요.")
    except requests.exceptions.Timeout:
        return TZInfo(error="⚠️ 요청 시간 초과 (10초).")
    except Exception as e:
        return TZInfo(error=f"❌ 예기치 않은 오류: {e}")


# ────────────────────────────── 공개 인터페이스 ───────────────────────────────

def fetch_terror_zone(token: str) -> TZInfo:
    """
    d2tz.info에서 공포구역 정보를 가져옵니다.

    Args:
        token: API 토큰

    Returns:
        TZInfo 객체
    """
    if not token:
        return TZInfo(error="⚠️ API 토큰이 설정되지 않았습니다.\n우클릭 → 설정에서 토큰을 입력해주세요.")
    return _fetch_d2tz(token)


# ────────────────────────────── 내부 헬퍼 ────────────────────────────────────

def _next_hour_timestamp() -> float:
    """다음 정각의 Unix timestamp를 반환합니다 (공포구역은 매 정각 갱신)."""
    now = time.time()
    return (int(now // 3600) + 1) * 3600
