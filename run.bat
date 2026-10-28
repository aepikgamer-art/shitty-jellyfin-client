@echo off
rem the "installer": launches the python client. python + VLC are signed/trusted,
rem so Smart App Control does not have a meltdown.
pip show python-vlc >nul 2>&1 || pip install python-vlc
pip show pillow >nul 2>&1 || pip install pillow
start "" pythonw "%~dp0client.py"
