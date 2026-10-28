@echo off
rem "the installer". it opens edge in app mode. that's the whole client.
start "" msedge --app="file:///%~dp0index.html"
