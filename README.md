# shitty-jellyfin-client

A deliberately janky, zero-polish Jellyfin media player client for Windows.

## Why

Because the official clients are too good and I needed something worse.

## Features

- [x] Logs in to a Jellyfin server (barely)
- [x] Lists your movies in a boring sidebar
- [x] Plays video INSIDE the app (via LibVLC, we outsourced the hard part)
- [x] A seek bar (it even works, mostly)
- [ ] Aesthetics
- [ ] Bug-free experience
- [ ] Subtitles, audio track selection, or respect

## Build

Requires .NET 8 SDK (Windows):

    dotnet publish -c Release

## Run

1. Type your server URL (e.g. http://192.168.1.10:8096)
2. Username + password, hit Login
3. Click a movie. It plays in the actual window now. Progress.

## Disclaimer

This is a joke-tier client. Use the real ones if you want subtitles, audio track pickers, or happiness.
