@echo off
rem the "installer": launches the powershell client. no sdk, no browser, no regrets.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0client.ps1"
