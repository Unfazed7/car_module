from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
from Crypto.Random import get_random_bytes

SECRET_KEY = b'sixteenbytekey!!'  # 16-byte key for AES + HMAC

def encrypt_frame(frame_id, data, counter=0):
    iv = get_random_bytes(16)

    # ⬅️ Convert counter to 2-byte and prepend to payload
    counter_bytes = counter.to_bytes(2, 'big')
    data_with_counter = counter.to_bytes(2, 'big') + data


    # ✅ Pad to 16-byte block size (PKCS7-like)
    pad_len = 16 - (len(data_with_counter) % 16)
    padded = data_with_counter + bytes([pad_len]) * pad_len

    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded)

    id_bytes = frame_id.to_bytes(2, 'big')
    h = HMAC.new(SECRET_KEY, iv + id_bytes + encrypted, digestmod=SHA256)
    mac = h.digest()[:6]

    return iv + id_bytes + encrypted + mac


def decrypt_frame(payload):
    if len(payload) != 40:
        raise ValueError(f"Encrypted frame length must be 40, got {len(payload)}")

    iv = payload[:16]
    frame_id_bytes = payload[16:18]
    encrypted = payload[18:-6]
    mac = payload[-6:]

    if len(encrypted) % 16 != 0:
        raise ValueError("Encrypted data must be multiple of 16 bytes")

    # 🔐 Verify HMAC
    h = HMAC.new(SECRET_KEY, iv + frame_id_bytes + encrypted, digestmod=SHA256)
    expected_mac = h.digest()[:6]
    if mac != expected_mac:
        raise ValueError("Invalid HMAC: Message tampered or forged")

    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(encrypted)

    # 🧽 Remove padding
    pad_len = decrypted_padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid padding length")
    decrypted = decrypted_padded[:-pad_len]

    # ✅ Extract counter and actual data
    counter = int.from_bytes(decrypted[:2], 'big')
    pure_data = decrypted[2:]

    frame_id = int.from_bytes(frame_id_bytes, 'big')
    return frame_id, pure_data, counter
