# shitty-jellyfin-client

A deliberately janky, zero-polish Jellyfin media player client for Windows. Now agent-maintained, so the jank is at least *organized* jank.

## Features

- [x] No .NET SDK, no browser, no web app
- [x] Python + tkinter + VLC: signed, trusted apps, coexists with Smart App Control
- [x] Native window, embedded VLC playback INSIDE the app
- [x] Poster thumbnails in the sidebar (needs pillow)
- [x] Search box that actually filters
- [x] Subtitles (best-effort, first external text track)
- [x] Volume slider + stop button + time display
- [x] Keyboard shortcuts: `space` pause, `←/→` seek 10s, `↑/↓` volume, `esc` exit fullscreen
- [x] Double-click video for fullscreen
- [x] Remembers your server + username in `config.json`
- [ ] Aesthetics
- [ ] Audio track selection, or respect

## Requirements

- [Python](https://python.org) (tick 'Add to PATH' when installing)
- [VLC](https://videolan.org)
- `pip install python-vlc pillow` (run.bat does it for u if missing)

## Run

Double-click `run.bat`.

## Disclaimer

This is a joke-tier client. Use the real ones if you want happiness.
