# shitty-jellyfin-client

A deliberately janky, zero-polish Jellyfin media player client for Windows.

## Why

Because the official clients are too good and I needed something worse.

## Features

- [x] No .NET SDK, no build, no install, nothing. One HTML file and a .bat
- [x] Logs in to a Jellyfin server (barely)
- [x] Lists your stuff in a sidebar with zero posters
- [x] Plays video INSIDE the player (it's a `<video>` tag. we are not writing a decoder)
- [x] Seek/volume/fullscreen = whatever the browser gives us for free
- [ ] Aesthetics
- [ ] Subtitles, audio track selection, or respect

## Run

Double-click `run.bat`. That's it. That's the install.

If your browser refuses `file://` fetch() calls (looking at you, Chrome), run it with Edge (the .bat already does) or host it anywhere static.

## Disclaimer

This is a joke-tier client. Use the real ones if you want happiness.
