#!/usr/bin/env python3
import can
import subprocess
import sys
from pathlib import Path
import cantools
from aes_utils import encrypt_frame

# Constants
CAN_INTERFACE = "vcan0"
DBC_FILES = ["demo1.dbc", "demo2.dbc", "demo3.dbc", "demo4.dbc"]
COUNTER_FILE = "msg_counter.txt"

# 🔁 Setup vcan0 if needed
def setup_vcan():
    try:
        subprocess.run(["ip", "link", "show", CAN_INTERFACE], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("🔧 Setting up vcan0...")
        subprocess.run(["sudo", "modprobe", "vcan"])
        subprocess.run(["sudo", "ip", "link", "add", "dev", CAN_INTERFACE, "type", "vcan"])
        subprocess.run(["sudo", "ip", "link", "set", "up", CAN_INTERFACE])
        print("✅ vcan0 ready.")

# 📘 Load/save counter
def load_counter():
    if Path(COUNTER_FILE).exists():
        return int(Path(COUNTER_FILE).read_text().strip())
    return 0

def save_counter(counter):
    Path(COUNTER_FILE).write_text(str(counter))

# 📚 Load correct DBC based on counter
def load_dbc(counter):
    dbc_path = DBC_FILES[(counter // 1) % len(DBC_FILES)]
    print(f"📘 Using DBC: {dbc_path}")
    return cantools.database.load_file(dbc_path)

# 🔐 Encrypt and send signal
def send_mapped_signal(db, cmd, counter):
    msg_def = db.get_message_by_name(cmd["message"])
    signal_vals = {sig.name: 0 for sig in msg_def.signals}
    signal_vals.update(cmd["signals"])
    raw_data = msg_def.encode(signal_vals)

    print(f"[ℹ] Raw data ({len(raw_data)}): {raw_data.hex()}")

    encrypted = encrypt_frame(msg_def.frame_id, raw_data, counter)
    print(f"[🔐] Encrypted ({len(encrypted)} bytes): {encrypted.hex()}")

    chunks = [encrypted[i:i+8] for i in range(0, len(encrypted), 8)][:5]

    with can.Bus(interface='socketcan', channel=CAN_INTERFACE) as bus:
        for i, chunk in enumerate(chunks):
            padded_chunk = chunk.ljust(8, b'\x00')
            arb_id = 0x7FF - i
            bus.send(can.Message(arbitration_id=arb_id, data=padded_chunk, is_extended_id=False))
            print(f"📤 Sent chunk {i}: ID={hex(arb_id)} Data={padded_chunk.hex()}")

# 🚀 Handle command
def handle_command(cmd_name):
    setup_vcan()
    counter = load_counter()

    commands = {
        "engine_on": {"message": "STATUS_CCAN3", "signals": {
            "EngineSts": 1, "EngineWaterTemp": 50, "EngineWaterTempFailSts": 0}},
        "engine_off": {"message": "STATUS_CCAN3", "signals": {
            "EngineSts": 0, "EngineWaterTemp": 50, "EngineWaterTempFailSts": 0}},
        "bonnet_open": {"message": "EXTERNAL_LIGHTS", "signals": {"BonnetSts": 1}},
        "bonnet_close": {"message": "EXTERNAL_LIGHTS", "signals": {"BonnetSts": 0}},
        "door_open": {"message": "STATUS_BH_BCM1", "signals": {"DriverDoorSts": 1}},
        "door_close": {"message": "STATUS_BH_BCM1", "signals": {"DriverDoorSts": 0}},
        "headlamp_on": {"message": "EXTERNAL_LIGHTS", "signals": {"LowBeamSts": 1}},
        "headlamp_off": {"message": "EXTERNAL_LIGHTS", "signals": {"LowBeamSts": 0}},
        "left_ind_on": {"message": "EXTERNAL_LIGHTS", "signals": {"LHTurnSignalSts": 1}},
        "left_ind_off": {"message": "EXTERNAL_LIGHTS", "signals": {"LHTurnSignalSts": 0}},
        "right_ind_on": {"message": "EXTERNAL_LIGHTS", "signals": {"RHTurnSignalSts": 1}},
        "right_ind_off": {"message": "EXTERNAL_LIGHTS", "signals": {"RHTurnSignalSts": 0}},
    }

    if cmd_name not in commands:
        print(f"❌ Unknown command: {cmd_name}")
        return False

    db = load_dbc(counter)
    send_mapped_signal(db, commands[cmd_name], counter)
    counter += 1
    save_counter(counter)
    return True

# CLI entry
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 ex1.py <command>")
        sys.exit(1)

    cmd = sys.argv[1]
    success = handle_command(cmd)
    if success:
        print(f"✅ Command '{cmd}' sent.")
    else:
        print(f"❌ Failed to send '{cmd}'")
