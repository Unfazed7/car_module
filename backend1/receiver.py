import can
import socketio
import time
from aes_utils import decrypt_frame
from pathlib import Path
from collections import deque
import subprocess

# ------------------ VCAN Setup ------------------ #
def setup_vcan():
    try:
        subprocess.check_output(["ip", "link", "show", "vcan0"], stderr=subprocess.STDOUT)
        print("🔌 vcan0 already exists.", flush=True)
    except subprocess.CalledProcessError:
        print("🔧 Setting up vcan0 interface...", flush=True)
        try:
            subprocess.run(["sudo", "modprobe", "vcan"], check=True)
            subprocess.run(["sudo", "ip", "link", "add", "dev", "vcan0", "type", "vcan"], check=True)
            subprocess.run(["sudo", "ip", "link", "set", "up", "vcan0"], check=True)
            print("✅ vcan0 interface created successfully.", flush=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to set up vcan0: {e}", flush=True)
            exit(1)

# ------------------ Socket.IO ------------------ #
sio = socketio.Client()
sio.connect("http://localhost:5001")
print("✅ Connected to Socket.IO", flush=True)

# ------------------ Constants ------------------ #
CAN_INTERFACE = "vcan0"
COUNTER_FILE = "last_counter.txt"
ALERT_FILE = "replay_alert.txt"
recent_messages = deque(maxlen=20)

# ------------------ Animation Mapping ------------------ #
animation_map = {
    ("0x12c", "0000008000000000"): (["Doors_LAction", "Doors_RAction"], False),
    ("0x258", "0000008000000000"): (["Doors_LAction", "Doors_RAction"], False),
    ("0x320", "0000008000000000"): (["Doors_LAction", "Doors_RAction"], False),
    ("0x356", "0000008000000000"): (["Doors_LAction", "Doors_RAction"], False),

    ("0x12c", "0000000000000000"): (["Doors_LAction", "Doors_RAction"], True),
    ("0x258", "0000000000000000"): (["Doors_LAction", "Doors_RAction"], True),
    ("0x320", "0000000000000000"): (["Doors_LAction", "Doors_RAction"], True),
    ("0x356", "0000000000000000"): (["Doors_LAction", "Doors_RAction"], True),

    ("0x354", "00000004"): (["hoodAction"], False),
    ("0x2bc", "00000004"): (["hoodAction"], False),
    ("0x1f4", "00000004"): (["hoodAction"], False),
    ("0x190", "00000004"): (["hoodAction"], False),

    ("0x354", "00000000"): (["hoodAction"], True),
    ("0x2bc", "00000000"): (["hoodAction"], True),
    ("0x1f4", "00000000"): (["hoodAction"], True),
    ("0x190", "00000000"): (["hoodAction"], True),

    ("0x403", "5a00000000000100"): (["chromeAction"], False),
}

# ------------------ Helpers ------------------ #
def is_duplicate(key, ttl=0.3):
    now = time.time()
    for k, t in recent_messages:
        if key == k and now - t < ttl:
            return True
    recent_messages.append((key, now))
    return False

def load_last_counter():
    try:
        return int(Path(COUNTER_FILE).read_text())
    except:
        return -1

def save_last_counter(counter):
    Path(COUNTER_FILE).write_text(str(counter))

def write_alert(msg):
    Path(ALERT_FILE).write_text(msg)

# ------------------ Main ------------------ #
setup_vcan()
last_counter = load_last_counter()
buffer = b""

print("🔐 Listening for encrypted CAN frames...", flush=True)

try:
    with can.interface.Bus(channel=CAN_INTERFACE, interface='socketcan') as bus:
        for msg in bus:
            buffer += msg.data
            print(f"[RX] {hex(msg.arbitration_id)} → {msg.data.hex()} ({len(buffer)}/40 bytes)", flush=True)

            if len(buffer) < 40:
                continue
            elif len(buffer) > 40:
                print("⚠️ Extra bytes detected, resetting buffer", flush=True)
                buffer = b""
                continue

            try:
                print(f"[🧪] Decrypting payload: {buffer.hex()}", flush=True)
                frame_id, decrypted, counter = decrypt_frame(buffer)
                frame_id_str = hex(frame_id).lower()
                payload_str = decrypted.hex().lower()
                key = (frame_id_str, payload_str)

                if is_duplicate(key):
                    print("⚠️ Duplicate detected, skipping", flush=True)
                    buffer = b""
                    continue

                if last_counter - counter > 100 and counter < 20:
                    print(f"[ℹ] Auto-resetting last_counter from {last_counter} → {counter}", flush=True)
                    last_counter = counter - 1

                if counter <= last_counter:
                    print(f"[⚠️] Replay attack detected: counter={counter}, last={last_counter}", flush=True)
                    write_alert("replay")
                    sio.emit("security_alert", {
                        "type": "replay_attack",
                        "can_id": frame_id_str,
                        "data": payload_str,
                        "counter": counter
                    })

                else:
                    print(f"[✔] Decrypted: ID={frame_id_str} Data={payload_str} Counter={counter}", flush=True)
                    write_alert("none")
                    last_counter = counter
                    save_last_counter(last_counter)

                    if key in animation_map:
                        animations, reverse = animation_map[key]
                        clean_animations = [str(name) for name in animations]

                        payload = {
                            "animations": clean_animations,
                            "reverse": reverse,
                            "can_id": frame_id_str,
                            "data": payload_str
                        }

                        sio.emit("frontend_animation", payload)
                        print(f"🎬 Emitted to frontend → {payload}", flush=True)
                    else:
                        print(f"⚠️ No animation mapped for {key}", flush=True)

            except Exception as e:
                print(f"[❌] Decryption or mapping error: {e}", flush=True)
                write_alert("decryption_failed")
                sio.emit("security_alert", {
                    "type": "tamper_detected",
                    "error": str(e)
                })

            finally:
                buffer = b""

except OSError as e:
    print(f"❌ Failed to open CAN interface: {e}", flush=True)
