import asyncio
import socket
import logging
from typing import Optional, Tuple, NamedTuple
from services.models import DeviceInfo

# loging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("H806SB")

class LedDiscoveryService:
    DEVICE_PORT = 4626
    LISTEN_PORT = 4882
    DISCOVERY_PACKET = bytes([0xAB, 0x01])
    RESPONSE_HEADER = bytes([0xAB, 0x02])

    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.bind(("0.0.0.0", self.LISTEN_PORT))
        self._sock.settimeout(3.0)

    async def discover_device(self, timeout: float = 3.0) -> Optional[DeviceInfo]:
        try:
            # send discovery-req
            self._sock.sendto(self.DISCOVERY_PACKET, ("<broadcast>", self.DEVICE_PORT))
            await asyncio.sleep(0.05)
            self._sock.sendto(self.DISCOVERY_PACKET, ("<broadcast>", self.DEVICE_PORT))

            # waiting answer
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    data, addr = await asyncio.get_event_loop().sock_recvfrom(self._sock, 1024)
                    if data.startswith(self.RESPONSE_HEADER):
                        # parsing
                        name_data = data[2:]
                        name = name_data.split(b'\x00')[0].decode("ascii")
                        
                        if "_" in name:
                            _, hex_part = name.split("_", 1)
                            serial = bytes.fromhex(hex_part)
                            return DeviceInfo(addr[0], serial, name)
                except socket.timeout:
                    continue

        except Exception as e:
            logger.error(f"Discovery error: {e}")
        return None

    def close(self):
        self._sock.close()