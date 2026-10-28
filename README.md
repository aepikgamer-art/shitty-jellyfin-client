# shitty-jellyfin-client

A deliberately janky, zero-polish Jellyfin media player client for Windows.

## Why

Because the official clients are too good and I needed something worse.

## Features

- [x] No .NET SDK, no browser, no web app
- [x] Python + tkinter + VLC: signed, trusted apps, coexists with Smart App Control
- [x] Native window, video plays INSIDE the app (embedded VLC)
- [x] Seek bar (a polling hack, but it works)
- [x] Play/pause button
- [ ] Aesthetics
- [ ] Subtitles, audio track selection, or respect

## Requirements

- [Python](https://python.org) (tick 'Add to PATH' when installing)
- [VLC](https://videolan.org)
- `pip install python-vlc` (run.bat does it for u if it's missing)

## Run

Double-click `run.bat`. It installs python-vlc if needed, then launches the client.

## Disclaimer

This is a joke-tier client. Use the real ones if you want happiness.
