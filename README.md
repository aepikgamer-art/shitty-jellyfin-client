# shitty-jellyfin-client

A deliberately janky, zero-polish Jellyfin media player client for Windows.

## Why

Because the official clients are too good and I needed something worse.

## Features

- [x] Logs in to a Jellyfin server (barely)
- [x] Lists your movies (in a boring grid)
- [x] Plays stuff by shelling out to your browser
- [ ] Aesthetics
- [ ] Bug-free experience

## Build

Requires .NET 8 SDK (Windows):

    dotnet publish -c Release

## Run

1. Type your server URL (e.g. http://192.168.1.10:8096)
2. Username + password, hit Login
3. Double-click a movie. It opens in your browser. That's the player. Don't ask questions.

## Disclaimer

This is a joke-tier client. Use the real ones if you want subtitles, seek controls, remote control support, or happiness.
