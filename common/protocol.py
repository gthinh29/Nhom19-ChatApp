import struct
import json

# --- CONSTANTS ---
HEADER_FORMAT = "!I"  # 4 bytes for length (Network byte order - Big Endian)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Commands
CMD_LOGIN = "LOGIN"
CMD_REGISTER = "REGISTER"
CMD_MSG = "MSG"
CMD_FILE = "FILE"      # FILE|INIT, FILE|CHUNK, FILE|END
CMD_IMAGE = "IMAGE"
CMD_LIST = "LIST"      # List online users
CMD_PING = "PING"
CMD_PONG = "PONG"

# Separator
SEPARATOR = "|"

def pack_packet(cmd: str, payload: str = "") -> bytes:
    """
    Pack a message into a length-prefixed packet.
    Format: [Length (4 bytes)][CMD|Payload]
    """
    content = f"{cmd}{SEPARATOR}{payload}"
    content_bytes = content.encode('utf-8')
    length = len(content_bytes)
    header = struct.pack(HEADER_FORMAT, length)
    return header + content_bytes

def unpack_packet(header: bytes, payload: bytes):
    """
    Unpack raw bytes into (cmd, payload_content).
    """
    # Header logic is handled by the receiver loop reading 4 bytes first
    # This function assumes we already have the full payload body
    try:
        content = payload.decode('utf-8')
        parts = content.split(SEPARATOR, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            return parts[0], ""
        else:
            return None, None
    except Exception as e:
        print(f"[PROTOCOL] Error unpacking: {e}")
        return None, None