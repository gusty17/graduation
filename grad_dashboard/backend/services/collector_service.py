"""
Training-data collector — driven from the dashboard.

Reuses the backend's single UDP socket (udp_service.py) so there is no port
conflict with the standalone udp_collector.py. While a collection is active the
UDP listener routes every packet here and pauses the live prediction/GCS
pipeline; each row is streamed to collecting/<session>/<label>.csv in the exact
format processing.py expects.

Receiver id is resolved by SENDER IP (like udp_collector.py — the in-packet ESP
id is unreliable on real hardware), falling back to the packet id for the local
fake publisher on 127.0.0.1.
"""

import os
import re
import csv
import time
import threading

# Where the training CSVs live: <repo>/grad_model_training/collecting/
COLLECT_ROOT = os.environ.get(
    "COLLECT_ROOT",
    os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "grad_model_training", "collecting",
    )),
)

# New firmware emits one fixed CSI length; drop anything else so a stray
# legacy/STBC frame can't contaminate a clean capture (matches udp_collector).
EXPECTED_CSI_LEN = int(os.environ.get("COLLECT_EXPECTED_CSI_LEN", "256"))
ENFORCE_LEN = os.environ.get("COLLECT_ENFORCE_LEN", "1") == "1"

# Sender IP -> receiver id. Same map as udp_collector.py.
DEVICE_MAP = {
    "192.168.8.88":  "rx1",
    "192.168.8.113": "rx2",
    "192.168.8.2":   "rx3",
}

LABELS = ("0p", "1p", "2p")            # processing.py class files
RECEIVERS = ("rx1", "rx2", "rx3")
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]+$")
MIN_DURATION, MAX_DURATION = 10, 3600

_lock = threading.Lock()
_file = None
_writer = None
_timer = None

_state = {
    "active": False,
    "label": None,
    "session": None,
    "path": None,
    "start": None,
    "duration": 0,
    "counts": {"rx1": 0, "rx2": 0, "rx3": 0, "unknown": 0, "dropped_len": 0},
    "summary": None,            # populated when a run stops
}


def _empty_counts():
    return {"rx1": 0, "rx2": 0, "rx3": 0, "unknown": 0, "dropped_len": 0}


def resolve_esp_id(sender_ip, device_id_raw):
    """Resolve the receiver id. The current sender.c stamps a reliable per-board
    device_id ("rx1"/"rx2"/"rx3"), so prefer that — it's immune to DHCP IP
    changes. Fall back to the sender-IP map only if the packet id is missing or
    unrecognized."""
    decoded = device_id_raw.decode(errors="ignore").strip("\x00").lower()
    if decoded in RECEIVERS:
        return decoded
    return DEVICE_MAP.get(sender_ip, decoded or "unknown")


# ── Session discovery ──────────────────────────────────────────────────────────
def list_sessions():
    if not os.path.isdir(COLLECT_ROOT):
        return []
    return sorted(
        d for d in os.listdir(COLLECT_ROOT)
        if d.startswith("session_") and os.path.isdir(os.path.join(COLLECT_ROOT, d))
    )


def sessions_detail():
    """Each session + which labels are already recorded (so the UI can warn on
    overwrite and show what's still missing)."""
    out = []
    for s in list_sessions():
        present = [lb for lb in LABELS
                   if os.path.exists(os.path.join(COLLECT_ROOT, s, f"{lb}.csv"))]
        out.append({"session": s, "labels": present})
    return out


def suggest_next_session():
    nums = [int(m.group(1)) for s in list_sessions()
            if (m := re.match(r"session_(\d+)$", s))]
    nxt = (max(nums) + 1) if nums else 1
    return f"session_{nxt:02d}"


# ── Lifecycle ──────────────────────────────────────────────────────────────────
def start_collection(label, session, duration):
    global _file, _writer, _timer

    if label not in LABELS:
        raise ValueError(f"label must be one of {list(LABELS)}")
    session = (session or "").strip()
    if not SESSION_RE.match(session):
        raise ValueError("session name may only contain letters, digits, '_' and '-'")
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        raise ValueError("duration must be a number of seconds")
    duration = max(MIN_DURATION, min(duration, MAX_DURATION))

    with _lock:
        if _state["active"]:
            raise RuntimeError("a collection is already in progress")
        session_dir = os.path.join(COLLECT_ROOT, session)
        os.makedirs(session_dir, exist_ok=True)
        path = os.path.join(session_dir, f"{label}.csv")
        _file = open(path, "w", newline="")
        _writer = csv.writer(_file)
        _writer.writerow(["esp_id", "timestamp", "rssi", "csi"])
        _file.flush()
        _state.update(
            active=True, label=label, session=session, path=path,
            start=time.time(), duration=duration, summary=None,
            counts=_empty_counts(),
        )
        print(f"🎬 COLLECT: recording {label} -> {path} for {duration}s")

    _timer = threading.Timer(duration, lambda: stop_collection(reason="duration"))
    _timer.daemon = True
    _timer.start()
    return status()


def record(esp_id, timestamp, rssi, csi_array, csi_len):
    """Write one row if a collection is active. Returns True when collection is
    active (so the caller skips the live pipeline), False otherwise."""
    with _lock:
        if not _state["active"]:
            return False
        if ENFORCE_LEN and csi_len != EXPECTED_CSI_LEN:
            _state["counts"]["dropped_len"] += 1
            return True
        _writer.writerow([esp_id, timestamp, int(rssi), str(csi_array)])
        _file.flush()
        key = esp_id if esp_id in RECEIVERS else "unknown"
        _state["counts"][key] += 1
        return True


def stop_collection(reason="manual"):
    global _file, _writer, _timer

    with _lock:
        if not _state["active"]:
            return _state["summary"]
        _state["active"] = False
        try:
            _file.close()
        except Exception:
            pass
        _file = None
        _writer = None

        counts = dict(_state["counts"])
        total = counts["rx1"] + counts["rx2"] + counts["rx3"]
        weakest = min(counts["rx1"], counts["rx2"], counts["rx3"])
        summary = {
            "label": _state["label"],
            "session": _state["session"],
            "path": _state["path"],
            "rows": total,
            "counts": counts,
            "weakest": weakest,
            "ok": weakest > 0,
            "reason": reason,
        }
        _state["summary"] = summary
        print(f"🛑 COLLECT: stopped ({reason}). rows={total} "
              f"rx1={counts['rx1']} rx2={counts['rx2']} rx3={counts['rx3']} "
              f"dropped_len={counts['dropped_len']} -> {summary['path']}")

    if _timer:
        _timer.cancel()
        _timer = None
    return summary


def status():
    with _lock:
        active = _state["active"]
        elapsed = int(time.time() - _state["start"]) if (active and _state["start"]) else 0
        duration = _state["duration"]
        return {
            "active": active,
            "label": _state["label"] if active else None,
            "session": _state["session"] if active else None,
            "duration": duration,
            "elapsed": elapsed,
            "remaining": max(0, duration - elapsed) if active else 0,
            "counts": dict(_state["counts"]),
            "summary": _state["summary"],
        }
