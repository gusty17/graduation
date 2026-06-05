import sys
import os

#  Add backend path
sys.path.append(os.path.abspath("../grad_dashboard/backend"))

import pandas as pd
import glob

# Import shared feature engineering
from common.feature_engineering import (
    preprocess_raw_csv,
    split_and_merge,
    build_window_features,
    WINDOW_SIZE
)

#from common.all_csi_data import (
#    preprocess_raw_csv,
#    split_and_merge,
#    build_window_features,
#    WINDOW_SIZE
#)

#from common.selected_index import (
#    preprocess_raw_csv,
#    split_and_merge,
#    build_window_features,
#    WINDOW_SIZE
#)

# ================= CONFIG =================
INPUT_DIR = "collecting"
OUTPUT_DIR = "combined"

os.makedirs(OUTPUT_DIR, exist_ok=True)

LABEL_MAP = {
    "No_person":      0,
    "point_1":        1,
    "point_2":        1,
    "point_3":        1,
    "point_1_2":      2,
    "point_1_3":      2,
    "point_2_3":      2,
    "point_1_2_3":    3,
}

# ================= DATASET BUILDER =================
def build_dataset(split):
    all_data = []

    for scenario, count in LABEL_MAP.items():
        folder = os.path.join(INPUT_DIR, split, scenario)

        print(f"\n📂 Processing scenario: {scenario} ({count} persons)")

        for file in glob.glob(os.path.join(folder, "*.csv")):
            print(f"   📄 File: {file}")

            try:
                # ================= LOAD =================
                df = preprocess_raw_csv(file)

                if df.empty:
                    print("   ⚠️ Empty after preprocessing")
                    continue

                # ================= MERGE RX1/RX2/RX3 =================
                merged = split_and_merge(df)

                if merged.empty or len(merged) < WINDOW_SIZE:
                    print(f"   ⚠️ Not enough merged samples: {len(merged)}")
                    continue

                print(f"   ✅ Merged samples: {len(merged)}")

                # ================= FEATURE EXTRACTION =================
                X, _ = build_window_features(merged)

                if X.empty:
                    print("   ⚠️ No features extracted")
                    continue

                print(f"   ✅ Extracted windows: {len(X)}")

                # ================= ADD LABELS =================
                X["scenario_id"] = scenario
                X["person_count"] = count

                all_data.append(X)

            except Exception as e:
                print(f"   ❌ Error processing {file}: {e}")
                continue

    if not all_data:
        print("❌ No data processed!")
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)

# ================= MAIN =================
if __name__ == "__main__":
    print("🚀 Building training dataset...")

    train_df = build_dataset("train")

    if train_df.empty:
        print("❌ Training dataset is empty!")
    else:
        output_path = os.path.join(OUTPUT_DIR, "train_dataset.csv")
        train_df.to_csv(output_path, index=False)

        print("\n✅ Dataset created successfully!")
        print(f"📁 Saved to: {output_path}")
        print(f"📊 Shape: {train_df.shape}")