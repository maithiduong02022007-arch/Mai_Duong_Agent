@echo off
title MINH AN AI AGENT CRM - LOCALHOST
echo ========================================================
echo  KHOI DONG HE THONG AI AGENT MINH AN TREN LOCALHOST
echo ========================================================
echo  Dang mo trinh duyet tai http://localhost:8080 ...
powershell -ExecutionPolicy Bypass -File "%~dp0server.ps1"
pause

