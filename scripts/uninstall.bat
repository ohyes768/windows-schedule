@echo off
REM ========================================
REM Python Task Scheduler 服务卸载脚本
REM ========================================

echo ========================================
echo Python Task Scheduler 服务卸载
echo ========================================
echo.

echo 正在停止服务...
nssm stop PyTaskSched

echo 正在删除服务...
nssm remove PyTaskSched confirm

echo.
echo ========================================
echo 服务已卸载
echo ========================================
echo.

pause
