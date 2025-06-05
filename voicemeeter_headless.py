import os
import ctypes
import json
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# DLL path
DLL_PATH = r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll"
voicemeeter = ctypes.WinDLL(DLL_PATH)

# Label ↔ index mapping
label_map = {
    0: "Bedroom",
    1: "Headphones",
    2: "Bathroom"
}
reverse_map = {v.lower(): k for k, v in label_map.items()}

class RemoteAPI:
    def __init__(self):
        print("Logging in to Voicemeeter API...")
        result = voicemeeter.VBVMR_Login()
        if result != 0:
            raise Exception("Login failed")
        print("✅ Login successful")

    def logout(self):
        voicemeeter.VBVMR_Logout()

    def set_gain(self, bus_index, value):
        param = f"Bus[{bus_index}].Gain".encode("utf-8")
        voicemeeter.VBVMR_SetParameterFloat(ctypes.c_char_p(param), ctypes.c_float(value))
        print(f"✔️ Set gain for bus {bus_index}: {value} dB")

    def set_mute(self, bus_index, state):
        param = f"Bus[{bus_index}].Mute".encode("utf-8")
        voicemeeter.VBVMR_SetParameterFloat(ctypes.c_char_p(param), ctypes.c_float(1.0 if state else 0.0))
        print(f"✔️ Set mute for bus {bus_index}: {'ON' if state else 'OFF'}")

    def get_status(self):
        status = {}
        for i in range(3):
            gain = ctypes.c_float()
            mute = ctypes.c_float()
            voicemeeter.VBVMR_GetParameterFloat(f"Bus[{i}].Gain".encode("utf-8"), ctypes.byref(gain))
            voicemeeter.VBVMR_GetParameterFloat(f"Bus[{i}].Mute".encode("utf-8"), ctypes.byref(mute))
            label = label_map.get(i, f"A{i+1}")
            status[label] = {
                "gain": round(gain.value, 2),
                "mute": bool(int(mute.value))
            }
        print("📡 STATUS RESPONSE:", json.dumps(status))
        return status

api = RemoteAPI()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
PORT = 5118

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        print("📥 GET:", self.path)
        if self.path == "/status":
            try:
                data = api.get_status()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                print("❌ Error in /status:", e)
                self.send_error(500, "Internal Server Error")
        elif self.path == "/panel":
            self.path = "/panel-v2.html"
            return SimpleHTTPRequestHandler.do_GET(self)
        else:
            return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)

        def resolve_bus(value):
            key = value.strip().lower()
            if key in reverse_map:
                return reverse_map[key]
            return int(value)

        if parsed.path == "/set_gain":
            try:
                bus = resolve_bus(q["bus"][0])
                value = float(q["value"][0])
                api.set_gain(bus, value)
                self.send_response(200)
                self.end_headers()
            except Exception as e:
                print("❌ Error in set_gain:", e)
                self.send_error(400, "Invalid gain params")
        elif parsed.path == "/set_mute":
            try:
                bus = resolve_bus(q["bus"][0])
                state = int(q["state"][0]) == 1
                api.set_mute(bus, state)
                self.send_response(200)
                self.end_headers()
            except Exception as e:
                print("❌ Error in set_mute:", e)
                self.send_error(400, "Invalid mute params")
        else:
            self.send_error(404)

def run_server():
    os.chdir(STATIC_DIR)
    server = HTTPServer(("", PORT), CustomHandler)
    print(f"🌐 Serving at http://localhost:{PORT}/panel")
    server.serve_forever()

if __name__ == "__main__":
    try:
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        thread.join()
    except KeyboardInterrupt:
        api.logout()
        print("🔒 Voicemeeter logged out.")
