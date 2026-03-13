@echo off
REM ============================================================
REM D2TZ Tracker - PyInstaller 빌드 스크립트
REM ============================================================
REM 사용법: build.bat 을 더블클릭하거나 cmd에서 실행
REM 결과물: dist\D2TZ_Tracker.exe
REM ============================================================

echo [D2TZ Tracker] Building .exe ...

REM 이전 빌드 정리
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist D2TZ_Tracker.spec del /q D2TZ_Tracker.spec

REM PyInstaller 빌드
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name D2TZ_Tracker ^
    --add-data "core;core" ^
    --add-data "api;api" ^
    --add-data "ui;ui" ^
    app.py

echo.
if exist dist\D2TZ_Tracker.exe (
    echo [SUCCESS] dist\D2TZ_Tracker.exe 생성 완료!
) else (
    echo [FAILED] 빌드 실패. 오류를 확인하세요.
)
pause
