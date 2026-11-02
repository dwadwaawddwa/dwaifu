@echo off
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -X utf8 -m kawaii %*
