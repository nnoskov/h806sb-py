import asyncio
import socket
import logging
from services.discovery import LedDiscoveryService

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("H806SB")

class LedController:
    def __init__(self):
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._broadcast_addr = ("<broadcast>", 4626)
        self._command_counter = 0
        
        # base packet
        self.packet = bytearray([
            0xFB, 0xC1,              # Command bytes
            0x00,                    # Counter (will be increased)
            0x50,                    # Speed (by default 80)
            0x00,                    # Brightness (by default 0)
            0x01,                    # Single file playback
            0x00, 0xAE,              # Unknown bytes
            0x00, 0x00, 0x00, 0x00,  # Constants as serial number
            0x00, 0x00, 0x00, 0x00   # Serial number (will be filling after discovery)
        ])

    async def send_command(self):
        """Update packet values and sending to device."""
        self.packet[2] = (self.packet[2] + 1) % 256  # increments of counter
        self._udp_socket.sendto(self.packet, self._broadcast_addr)
        logger.debug(f"Sent packet: {self.packet.hex(' ')}")

    async def set_speed(self, speed: int):
        """Set speed (1-100)."""
        speed = max(1, min(100, speed))
        self.packet[3] = speed
        await self.send_command()

    async def set_brightness(self, brightness: int):
        """Set brightness (0-31)."""
        brightness = max(0, min(31, brightness))
        self.packet[4] = brightness
        await self.send_command()

    async def set_single_file(self, mode: int):
        """Set mode single file (0 or 1)."""
        mode = 1 if mode else 0
        self.packet[5] = mode
        await self.send_command()

    def has_serial_number(self) -> bool:
        """Checking the installation of the serial number after detection."""
        return any(self.packet[12:16])

    def close(self):
        self._udp_socket.close()

async def handle_set_command(controller: LedController, cmd: str, value: str):
    """Handling commands set."""
    if not controller.has_serial_number():
        print("Please, discovery the device. (discover)")
        return

    try:
        if cmd == "br":
            brightness = int(value)
            if 0 <= brightness <= 31:
                await controller.set_brightness(brightness)
                print(f"Brightness is set to: {brightness}/31")
            else:
                print("Incorrect brightness. Available range: 0-31")
        elif cmd == "sp":
            speed = int(value)
            if 1 <= speed <= 100:
                await controller.set_speed(speed)
                print(f"Speed is set to: {speed}/100")
            else:
                print("Incorrect speed. Available range: 1-100")
        elif cmd == "sf":
            mode = int(value)
            if mode in (0, 1):
                await controller.set_single_file(mode)
                print(f"Single file mode is: {mode}")
            else:
                print("Incorrect mode. Available values: 0 or 1")
        else:
            print("Unknown command. Available commands: br, sp, sf")
    except ValueError:
        print("Error: Value is number only")

async def main():

    controller = LedController()
    discovery = LedDiscoveryService()

    print("LED Controller (Python)")
    print("Commands:")
    print("  discover       - Finding of device")
    print("  set br <0-31>  - Set brightness (0-31)")
    print("  set sp <1-100> - Set speed (0-100)")
    print("  set sf <0-1>   - Set single file (0-1)")
    print("  exit           - Exit")

    try:
        while True:
            try:
                command = input("> ").strip().lower()
                if not command:
                    continue

                if command == "exit":
                    break

                elif command == "discover":
                    print("Discover of device...")
                    device = await discovery.discover_device()
                    if device:
                        print(f"Success! Device Name:: {device.device_name} (IP: {device.address})")
                        length = len(device.serial_number)
                        for i in range(length):
                            controller.packet[14 - i] = device.serial_number[i]
                        print(f"Packet:: {controller.packet.hex(' ')}")
                    else:
                        print("The Device not found. :(")

                elif command.startswith("set "):
                    parts = command.split()
                    if len(parts) == 3:
                        await handle_set_command(controller, parts[1], parts[2])
                    else:
                        print("Unknown command. Available: 'br <0-31>', 'sp <1-100>', 'sf <0-1>'")

                else:
                    print("Unknown command")

            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\nThe Operation has been cancelled")
                continue
            except Exception as e:
                print(f"Error: {e}")

    finally:
        controller.close()
        discovery.close()
        print("Program finished")

if __name__ == "__main__":
    asyncio.run(main())