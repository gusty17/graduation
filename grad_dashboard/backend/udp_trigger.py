"""
CSI trigger — generates the downlink WiFi traffic that makes the ESP receivers
capture CSI.

How it works: sender.c only produces a CSI frame when the ESP *receives* a WiFi
frame. Each UDP packet we send to an ESP's IP is delivered by the AP as a
unicast (HT/802.11n) frame → the ESP's CSI callback fires → it forwards one CSI
row to the laptop. No listener is needed on the ESP; only the destination IP
matters.

The ESPs get their IPs from DHCP, so hardcoding them breaks on every new lease.
Instead we AUTO-DISCOVER them by their Espressif MAC prefix from the ARP table,
and refresh periodically. Override with env vars if needed:
  ESP_STATIC_IPS="192.168.8.100,192.168.8.101,192.168.8.102"  # skip discovery
  ESP_OUI_PREFIXES="f8-b3-b7,84-cc-a8"                         # extra ESP OUIs
  ESP_SUBNET="192.168.8"   TRIGGER_RATE_HZ="50"
"""

import os
import re
import socket
import subprocess
import threading
import time

# ── Config ─────────────────────────────────────────────────────────────────────
SUBNET = os.environ.get("ESP_SUBNET", "192.168.8")           # /24 the ESPs live on
TRIGGER_PORT = int(os.environ.get("ESP_TRIGGER_PORT", "3333"))
PACKET_RATE_HZ = int(os.environ.get("TRIGGER_RATE_HZ", "5"))
REDISCOVER_EVERY = 5.0                                         # seconds between re-scans
# Keep triggering an ESP for this long after its last ARP sighting. ARP entries
# expire quickly, so a single scan rarely sees all 3 at once — we accumulate
# sightings and only drop an IP once it's been gone this long (handles DHCP).
TARGET_TTL = float(os.environ.get("ESP_TARGET_TTL", "120"))
MESSAGE = b"CSI_TRIGGER"

# Espressif MAC OUI prefixes as ARP prints them (xx-xx-xx). Your boards span two
# Espressif OUIs (f8-b3-b7 and f4-2d-c9); add more via ESP_OUI_PREFIXES if a
# board uses a different one.
ESP_OUI_PREFIXES = tuple(
    p.strip().lower().replace(":", "-")
    for p in os.environ.get("ESP_OUI_PREFIXES", "f8-b3-b7,f4-2d-c9").split(",")
    if p.strip()
)
# Manual override: if set, skip discovery and trigger exactly these IPs.
ESP_STATIC_IPS = [ip.strip() for ip in os.environ.get("ESP_STATIC_IPS", "").split(",") if ip.strip()]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

_ARP_LINE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F]{2}(?:[-:][0-9a-fA-F]{2}){5})")

_targets = []
_targets_lock = threading.Lock()

_seen = {}                 # esp ip -> last time it appeared in ARP as an ESP
_seen_lock = threading.Lock()


def _prime_arp():
    """Force ARP resolution across the /24 by sending a tiny UDP datagram to each
    host, so any powered-on ESP shows up in the ARP table for discovery."""
    for i in range(1, 255):
        try:
            sock.sendto(b"", (f"{SUBNET}.{i}", TRIGGER_PORT))
        except OSError:
            pass


def _scan_arp():
    """One ARP snapshot: return the ESP IPs currently visible (may be a subset —
    ARP entries for idle hosts expire quickly)."""
    _prime_arp()
    time.sleep(1.5)  # let the OS populate ARP replies
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    found = []
    for line in out.splitlines():
        m = _ARP_LINE.search(line)
        if not m:
            continue
        ip, mac = m.group(1), m.group(2).lower().replace(":", "-")
        if ip.startswith(SUBNET + ".") and mac[:8] in ESP_OUI_PREFIXES:
            found.append(ip)
    return found


def discover_esps():
    """Current ESP targets. Accumulates ARP sightings across scans (each snapshot
    may only catch a subset) and drops IPs unseen for TARGET_TTL so DHCP changes
    age out. Once we start triggering an ESP its ARP entry stays fresh."""
    if ESP_STATIC_IPS:
        return ESP_STATIC_IPS
    found = _scan_arp()
    now = time.time()
    with _seen_lock:
        for ip in found:
            _seen[ip] = now
        for ip in [k for k, v in list(_seen.items()) if now - v > TARGET_TTL]:
            del _seen[ip]
        return sorted(_seen)


def _discovery_loop():
    global _targets
    while True:
        found = discover_esps()
        with _targets_lock:
            if found and found != _targets:
                print(f"✅ ESP targets: {found}")
                _targets = found
            elif not found and not _targets:
                print(f"⚠ No ESPs found on {SUBNET}.0/24 "
                      f"(OUIs {list(ESP_OUI_PREFIXES)}). Powered on & on WiFi?")
        time.sleep(REDISCOVER_EVERY)


def main():
    print(f"Trigger: {PACKET_RATE_HZ} pkt/s/ESP on {SUBNET}.0/24 port {TRIGGER_PORT}")
    threading.Thread(target=_discovery_loop, daemon=True).start()

    interval = 1.0 / PACKET_RATE_HZ
    counter = 0
    time.sleep(1.5)  # give the first discovery a moment
    while True:
        with _targets_lock:
            targets = list(_targets)
        payload = MESSAGE + counter.to_bytes(4, "little")
        for ip in targets:
            try:
                sock.sendto(payload, (ip, TRIGGER_PORT))
            except OSError:
                pass
        counter += 1
        time.sleep(interval)


if __name__ == "__main__":
    main()
