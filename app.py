"""
app.py - D2R Terror Zone Overlay Tracker
엔트리포인트: 설정 로드 후 오버레이 창 실행.

사용법:
  python app.py

빌드:
  pyinstaller --onefile --noconsole --name D2TZ_Tracker app.py

API 토큰 발급:
  - d2runewizard.com: https://d2runewizard.com/integration
  - d2emu.com: https://discord.gg/yeFkxYdpru 에서 Discord 봇을 통해 요청
"""
import sys
import os

# PyInstaller .exe 환경에서 sys.path 보정
if getattr(sys, "frozen", False):
    # 실행 파일 기준 경로
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, _BASE)

from ui.overlay import OverlayApp


def main() -> None:
    app = OverlayApp()
    app.mainloop()


if __name__ == "__main__":
    main()
