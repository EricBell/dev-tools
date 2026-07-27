#!/usr/bin/env python3
"""Send a Wake-on-LAN magic packet.

Edit TARGET_IP and TARGET_MAC at the top as needed.
This script uses only the Python standard library, so it can be run with uv
without installing any extra packages.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from pathlib import Path

TARGET_IP = "192.168.1.137"
TARGET_MAC = "84:9e:56:07:fb:d3"
SUBNET_PREFIX = 24
BROADCAST_PORT = 9


def normalize_mac(mac: str) -> bytes:
    hex_digits = re.sub(r"[^0-9A-Fa-f]", "", mac)
    if len(hex_digits) != 12:
        raise ValueError(f"Invalid MAC address: {mac!r}")
    return bytes.fromhex(hex_digits)


def mac_from_arp_cache(ip: str) -> str | None:
    arp_path = Path("/proc/net/arp")
    if not arp_path.exists():
        return None

    lines = arp_path.read_text().splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 4 and parts[0] == ip:
            mac = parts[3]
            if mac != "00:00:00:00:00:00":
                return mac
    return None


def resolve_target_mac() -> str:
    if TARGET_MAC:
        return TARGET_MAC

    arp_mac = mac_from_arp_cache(TARGET_IP)
    if arp_mac:
        return arp_mac

    raise SystemExit(
        "Set TARGET_MAC in wake-on-lan/wol.py. "
        "Wake-on-LAN packets are addressed to a MAC address."
    )


def broadcast_address(ip: str, prefix: int) -> str:
    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    return str(network.broadcast_address)


def send_magic_packet(mac: str, destination: str, port: int) -> None:
    mac_bytes = normalize_mac(mac)
    packet = b"\xff" * 6 + mac_bytes * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (destination, port))


def main() -> None:
    mac = resolve_target_mac()
    destination = broadcast_address(TARGET_IP, SUBNET_PREFIX)
    send_magic_packet(mac, destination, BROADCAST_PORT)
    print(f"Sent Wake-on-LAN packet to {mac} via {destination}:{BROADCAST_PORT}")


if __name__ == "__main__":
    main()
