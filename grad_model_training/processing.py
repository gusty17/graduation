import sys
import os

#  Add backend path
sys.path.append(os.path.abspath("../grad_dashboard/backend"))

import glob
import joblib
import pandas as pd

# Import shared feature engineering
from common.preprocessing import (
    calibrate_null_subcarriers,
    load_and_clean,
    build_windows,
    compute_baseline,
    apply_baseline,
)

# ================= CONFIG =================
# New collection layout - one folder per recording loop/session, each holding
# the three class captures. The 0p capture in every session is recorded FIRST
# and doubles as that session's empty-room baseline:
#
#   collecting/
#     session_01/  0p.csv  1p.csv  2p.csv
#     session_02/  0p.csv  1p.csv  2p.csv
#     ...
#
# Keeping sessions separate lets the trainer hold out whole sessions (real
# cross-session generalization) and lets us baseline-normalize per session.
INPUT_DIR = "collecting"
MODELS_DIR = "../grad_dashboard/backend/models"
OUTPUT_CSV = "combined/engineered_csi_features.csv"

CLASS_FILES = {"0p.csv": 0, "1p.csv": 1, "2p.csv": 2}
BASELINE_LABEL = 0   # empty-room class used as each session's baseline
EXPECTED_LABELS = sorted(set(CLASS_FILES.values()))


def find_sessions():
    """Return {session_id: {label: filepath}} for every session_* folder."""
    sessions = {}
    for folder in sorted(glob.glob(os.path.join(INPUT_DIR, "session_*"))):
        if not os.path.isdir(folder):
            continue
        sid = os.path.basename(folder)
        files = {}
        for fname, label in CLASS_FILES.items():
            path = os.path.join(folder, fname)
            if os.path.exists(path):
                files[label] = path
        if files:
            sessions[sid] = files
    return sessions


# ================= PER-SESSION BUILDER =================
def build_session(sid, files, valid_mask):
    """Clean + window every class file in one session, then subtract that
    session's own empty-room baseline from all of its windows."""
    per_label = {}
    for label, path in sorted(files.items()):
        print(f"   📄 [{sid}] label {label}: {path}")
        try:
            cleaned, _ = load_and_clean(path, label=label, valid_mask=valid_mask)
        except Exception as e:
            print(f"      ❌ clean error: {e}")
            continue
        if cleaned.empty:
            print("      ⚠️ empty after cleaning")
            continue
        X = build_windows(cleaned, label=label)
        if X.empty:
            print("      ⚠️ no windows extracted")
            continue
        X["session_id"] = sid
        X["source_file"] = path
        print(f"      ✅ {len(X)} windows")
        per_label[label] = X

    if BASELINE_LABEL not in per_label:
        print(f"   ⛔ [{sid}] no empty-room ({BASELINE_LABEL}p) baseline windows "
              f"- skipping this session entirely")
        return None

    baseline = compute_baseline(per_label[BASELINE_LABEL])
    normalized = [apply_baseline(X, baseline) for X in per_label.values()]
    return pd.concat(normalized, ignore_index=True)


# ================= MAIN =================
if __name__ == "__main__":
    print("🚀 Building training dataset (session-aware, baseline-normalized)...")

    sessions = find_sessions()
    if not sessions:
        print(f"❌ No session_* folders found under {INPUT_DIR}/")
        print("   Expected: collecting/session_01/{0p,1p,2p}.csv, session_02/..., ...")
        sys.exit(1)

    print(f"\n🗂️  Found {len(sessions)} session(s): {list(sessions)}")

    all_files = [p for files in sessions.values() for p in files.values()]
    print(f"\n🔧 Calibrating null subcarriers across {len(all_files)} file(s)...")
    valid_mask = calibrate_null_subcarriers(all_files)
    joblib.dump(valid_mask, os.path.join(MODELS_DIR, "valid_mask.pkl"))
    print(f"✅ Saved valid_mask ({int(valid_mask.sum())} valid subcarriers) "
          f"to {os.path.join(MODELS_DIR, 'valid_mask.pkl')}")

    frames = []
    for sid, files in sessions.items():
        print(f"\n📂 Processing {sid}")
        out = build_session(sid, files, valid_mask)
        if out is not None and not out.empty:
            frames.append(out)

    if not frames:
        print("\n❌ No usable sessions produced any windows!")
        sys.exit(1)

    dataset_df = pd.concat(frames, ignore_index=True)

    # ================= GUARDS =================
    # Catch the failure mode that silently shipped a binary model last time:
    # a class that produced zero windows.
    present = sorted(dataset_df["label"].unique().tolist())
    missing = sorted(set(EXPECTED_LABELS) - set(present))

    print("\n================ DATASET SUMMARY ================")
    print(f"Sessions used : {dataset_df['session_id'].nunique()}")
    print(f"Total windows : {len(dataset_df)}")
    print("Label counts  :")
    print(dataset_df["label"].value_counts().sort_index().to_string())
    print("Windows per session/label:")
    print(dataset_df.groupby(["session_id", "label"]).size().to_string())

    if dataset_df["session_id"].nunique() < 2:
        print("\n⚠️  Only ONE session present. The model cannot be validated for "
              "cross-session generalization - collect multiple sessions.")
    if missing:
        print(f"\n❌ GUARD FAILED: no windows for label(s) {missing}. "
              f"Do NOT train on this dataset - investigate why those captures "
              f"produced no windows (often a weak/missing receiver).")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    dataset_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved to: {OUTPUT_CSV}")
    print(f"📊 Shape: {dataset_df.shape}")
