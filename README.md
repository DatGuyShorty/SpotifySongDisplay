# SpotifySongDisplay

SpotifySongDisplay is a Python application that displays the currently playing song and artist from your Spotify account on a 16x2 serial display (such as an LCD connected via a microcontroller). It runs in the system tray and communicates with Spotify and your display hardware.

## Features

- Displays the current song name and artist from Spotify
- System tray integration for easy access
- Serial communication with configurable port and baud rate
- Settings dialog for Spotify credentials and hardware configuration
- Update checker for new releases
- Error notifications and status icons

## Requirements

- Python 3.7+
- Spotify Developer account (for API credentials)
- Supported hardware for serial display (e.g., Arduino, Raspberry Pi, etc.)
- The following Python packages:
  - spotipy
  - pystray
  - pillow
  - requests
  - pyserial

Install dependencies with:

```sh
pip install spotipy pystray pillow requests pyserial
```

## Setup

1. Register a Spotify app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) to get your Client ID and Client Secret.
2. Clone or download this repository.
3. Run the application:

```sh
python SongDisplay.pyw
```

4. Open the Settings from the tray icon and enter your Spotify credentials, serial port, and other configuration options.
5. Connect your 16x2 display to the specified serial port.

## Usage

- The app will show a tray icon indicating connection status.
- Song and artist info will be sent to your display when music is playing.
- Use the tray menu to reconnect, disconnect, change settings, check for updates, or quit.

## Troubleshooting

- Ensure your serial port and baud rate match your hardware setup.
- Make sure your Spotify credentials are correct and the redirect URI matches your Spotify app settings.
- If you encounter errors, check the tray icon for status or error messages.


## Credits

Created by DatGuyShorty

