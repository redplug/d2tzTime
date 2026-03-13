# 🔥 D2TZ Tracker

디아블로2 레저렉션(D2R) **공포구역(Terror Zone)** 실시간 오버레이 트래커

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)](https://www.microsoft.com/windows)

---

## 📸 기능

- **현재 공포구역** 및 **다음 공포구역** 실시간 표시
- **MM:SS 카운트다운** (매 정각 자동 갱신)
- **구역명 한글/영문** 전환
- **프레임리스 오버레이** (타이틀바 없음, 게임 위에 표시)
- **투명도 조절** / **Always on Top** / **위치 고정**
- **우클릭 메뉴**로 설정 및 새로고침
- API 토큰은 `config.json`에 안전하게 난독화 저장

---

## 🚀 빠른 시작

### 1. API 토큰 발급

| 소스 | 발급 방법 |
|------|----------|
| **d2runewizard.com** (권장) | [d2runewizard.com/integration](https://d2runewizard.com/integration) 에서 신청 |
| **d2emu.com** | [Discord](https://discord.gg/yeFkxYdpru) 서버에서 신청 |

### 2. 실행

#### 방법 A: exe 파일 사용 (비개발자)
```
dist/D2TZ_Tracker.exe 를 실행
```

#### 방법 B: Python 직접 실행
```powershell
# 1. 가상환경 생성 (선택사항)
python -m venv .venv
.venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 실행
python app.py
```

### 3. 첫 실행
- 토큰이 없으면 자동으로 **설정 창**이 팝업됩니다
- API 소스 선택 후 토큰 입력 → 저장

---

## 🖱️ 조작법

| 동작 | 설명 |
|------|------|
| **드래그** | 창 이동 |
| **우클릭** | 컨텍스트 메뉴 (설정, 새로고침, 종료) |
| **✕ 버튼** | 종료 (위치 자동 저장) |

---

## 🔨 .exe 빌드

```powershell
# 방법 1: build.bat 더블클릭

# 방법 2: 직접 실행
pyinstaller --onefile --noconsole --name D2TZ_Tracker --add-data "core;core" --add-data "api;api" --add-data "ui;ui" app.py
```

빌드 결과: `dist/D2TZ_Tracker.exe`

---

## ⚠️ 주의사항

- `config.json`에는 난독화된 API 토큰이 저장됩니다. **절대 공유하지 마세요** (`.gitignore`로 제외됨)
- API 토큰은 d2runewizard/d2emu의 이용약관을 준수하여 사용하세요
- 공포구역 정보는 `d2runewizard.com` 또는 `d2emu.com` 서버에 의존합니다

---

## 📁 프로젝트 구조

```
d2tzTime/
├── app.py                  # 엔트리포인트
├── ui/
│   ├── overlay.py          # 오버레이 창
│   └── settings_dialog.py  # 설정 팝업
├── api/
│   └── client.py           # API 클라이언트
├── core/
│   ├── config.py           # 설정 저장/불러오기
│   └── tz_data.py          # 구역명 한글 매핑
├── requirements.txt
├── build.bat               # PyInstaller 빌드 스크립트
└── .gitignore
```

---

## 📄 License

MIT License © 2025
