@echo off
cd /d %~dp0
if exist venv\Scripts\activate call venv\Scripts\activate
start "" http://localhost:5000
python -m web.app
