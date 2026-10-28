@echo off
rem the "installer": launches the python client. needs python + VLC installed,
rem both signed and trusted, so Smart App Control does not have a meltdown.
pip show python-vlc >nul 2>&1 || pip install python-vlc
start "" pythonw "%~dp0client.py"
