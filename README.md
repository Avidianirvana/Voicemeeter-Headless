# VoiceMeeter Headless Control

This is a headless Python script that uses the VoiceMeeter Remote API (DLL) to control VoiceMeeter from a local or remote web interface.

## Features

- Load and control VoiceMeeter settings headlessly
- Serve a simple control panel via Flask
- Optional reconnection and status-checking support

## Requirements

- Windows (VoiceMeeter must be installed)
- Python 3.9+
- VoiceMeeterRemote64.dll available and accessible
- See `requirements.txt` for Python packages

## Usage

```bash
pip install -r requirements.txt
python voicemeeter_headless.py
