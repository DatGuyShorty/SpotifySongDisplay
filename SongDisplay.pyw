import threading
import time
import sys
import os
import json
import serial
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import messagebox

# ─── CONFIG FILE ───────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.spotify_pi_tray_config.json')
DEFAULT_CONFIG = {
    'client_id': '',
    'client_secret': '',
    'redirect_uri': 'http://127.0.0.1:8888',
    'cache_path': os.path.join(os.path.expanduser('~'), '.spotify_token_cache'),
    'serial_port': 'COM8',
    'baud_rate': 9600,
    'poll_interval': 5
}

# ─── ABOUT INFO ─────────────────────────────────────────────────────────────────
CREATOR_NAME = 'DatGuyShorty'
APP_VERSION = '0.2.1'
GITHUB_REPO = 'DatGuyShorty/SpotifySongDisplay'  # replace with your GitHub repo

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config, save_callback, update_callback):
        super().__init__(parent)
        self.title('Settings')
        self.resizable(False, False)
        self.config = config
        self.save_callback = save_callback
        self.update_callback = update_callback
        fields = [
            ('Spotify Client ID', 'client_id'),
            ('Spotify Client Secret', 'client_secret'),
            ('Redirect URI', 'redirect_uri'),
            ('Serial Port', 'serial_port'),
            ('Baud Rate', 'baud_rate'),
            ('Poll Interval (s)', 'poll_interval')
        ]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(self, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            entry = tk.Entry(self, width=40)
            entry.insert(0, str(self.config.get(key, '')))
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[key] = entry
        # About & version section
        row = len(fields)
        sep = tk.Frame(self, height=2, bd=1, relief='sunken')
        sep.grid(row=row, columnspan=2, sticky='we', pady=5)
        tk.Label(self, text=f'Creator: {CREATOR_NAME}').grid(row=row+1, column=0, columnspan=2)
        tk.Label(self, text=f'Version: {APP_VERSION}').grid(row=row+2, column=0, columnspan=2)
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=row+3, columnspan=2, pady=10)
        tk.Button(btn_frame, text='Save', command=self.on_save).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text='Update', command=self.on_update).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.destroy)

    def on_save(self):
        try:
            for key, entry in self.entries.items():
                val = entry.get().strip()
                if key in ['baud_rate', 'poll_interval']:
                    self.config[key] = int(val)
                else:
                    self.config[key] = val
            self.save_callback(self.config)
            self.destroy()
        except ValueError as e:
            messagebox.showerror('Invalid Input', str(e))

    def on_update(self):
        self.update_callback()

class TrayApp:
    def __init__(self):
        # Create a hidden root window for message boxes
        self.hidden_root = tk.Tk()
        self.hidden_root.withdraw()  # Hide the root window

        self.config = self._load_config()
        self.sp = None
        self.serial = None
        self.connected = False
        self.last_message = None
        self.last_state = None
        self.icon = pystray.Icon(
            'SpotifyDisplay',
            self._create_icon('grey'),
            'Disconnected',
            menu=pystray.Menu(
                item('Reconnect', self.reconnect),
                item('Disconnect', self.disconnect),
                item('Settings', self.show_settings),
                item('Quit', self.quit)
            )
        )
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._init_spotify()

    def _load_config(self):
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()

    def _save_config(self, new_config):
        self.config = new_config
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.config, f, indent=4)
        self._init_spotify()
        self.icon.notify('Settings saved. Please reconnect.')

    def _init_spotify(self):
        try:
            auth = SpotifyOAuth(
                client_id=self.config['client_id'],
                client_secret=self.config['client_secret'],
                redirect_uri=self.config['redirect_uri'],
                scope='user-read-playback-state',
                cache_path=self.config['cache_path'],
                show_dialog=False
            )
            self.sp = spotipy.Spotify(auth_manager=auth)
        except SpotifyOauthError as e:
            self.icon.notify(f'Auth Error: {e}')

    def _create_icon(self, color):
        img = Image.new('RGB', (64, 64), 'white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([(8, 8), (56, 56)], fill=color)
        return img

    def show_settings(self, *_):
        root = tk.Tk()
        root.withdraw()
        SettingsDialog(root, self.config.copy(), self._save_config, self.check_for_update)
        root.mainloop()
        root.destroy()

    def check_for_update(self):
        try:
            url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()  # Raise an error for HTTP issues
            data = resp.json()
            latest = data.get('tag_name')

            if latest and latest != APP_VERSION:
                if messagebox.askyesno('Update Available',
                                       f'Version {latest} is available. Download and install?'):
                    assets = data.get('assets', [])
                    if assets:
                        download_url = assets[0].get('browser_download_url')
                        if download_url:
                            import webbrowser
                            webbrowser.open(download_url)
                        else:
                            messagebox.showerror('Update Error', 'No download URL found.')
                    else:
                        messagebox.showerror('Update Error', 'No assets found for the update.')
            else:
                messagebox.showinfo('No Update', 'You are on the latest version.')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Update Error', f'Failed to check for updates: {e}')
        except Exception as e:
            messagebox.showerror('Update Error', f'An unexpected error occurred: {e}')

    def start(self):
        self.reconnect()
        self.poll_thread.start()
        self.icon.run()  # Start the system tray icon event loop
    def reconnect(self):
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
            self.serial = serial.Serial(
                self.config['serial_port'],
                self.config['baud_rate'],
                timeout=1
            )
            time.sleep(2)
            self.connected = True
            self.icon.icon = self._create_icon('green')
            self.icon.title = 'Connected'
            self.last_message = None
            self.last_state = None
        except Exception as e:
            self.connected = False
            self.icon.icon = self._create_icon('red')
            self.icon.title = f"Error: {e}"

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False
        self.icon.icon = self._create_icon('grey')
        self.icon.title = "Disconnected"

    def quit(self):
        self.disconnect()
        self.icon.stop()
        self.hidden_root.quit()  # Stop the Tkinter event loop
        self.hidden_root.destroy()  # Destroy the hidden root window

    def _poll_loop(self):
        while True:
            if self.connected and self.sp:
                try:
                    playback = self.sp.current_playback()
                    if not playback or not playback.get('item'):
                        state, msg = 'stopped', 'No song playing'
                    else:
                        track = playback['item']['name']
                        artists = ', '.join(a['name'] for a in playback['item']['artists'])
                        if playback.get('is_playing'):
                            state, msg = 'playing', f"{track} - {artists}"
                        else:
                            state, msg = 'paused', f"{track} - {artists} (Paused)"
                    if msg != self.last_message or state != self.last_state:
                        serial_msg = 'No song\n\n' if state=='stopped' else f"{track}\n{artists}\n\n"
                        try: self.serial.write(serial_msg.encode('utf-8'))
                        except: pass
                        color = 'green' if state=='playing' else ('grey' if state=='paused' else 'red')
                        self.icon.icon = self._create_icon(color)
                        self.icon.title = msg
                        self.last_message, self.last_state = msg, state
                except Exception as e:
                    self.icon.icon = self._create_icon('red')
                    self.icon.title = f'Error: {e}'
                    self.connected = False
            time.sleep(self.config['poll_interval'])

if __name__ == '__main__':
    TrayApp().start()
