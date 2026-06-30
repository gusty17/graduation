# ⚠️  EXACT COPY of grad_dashboard/backend/common/preprocessing.py — the cloud
# job must use the SAME clean/window/baseline code the model was trained and
# served with. If you change one, copy it to the other (Docker can only COPY
# files inside the pipeline/ build context, hence the duplicate).
import re
import numpy as np
import pandas as pd
from scipy.signal import stft

# ---------------------------------------------------------------------------
# Low-level CSI parsing and cleaning utilities
# ---------------------------------------------------------------------------

ELAPSED_RE = re.compile(r"^\d{1,3}:\d{2}\.\d+$")


def parse_timestamps(raw: pd.Series) -> np.ndarray:

    raw = raw.astype(str)
    sample = raw.dropna().head(50)
    if sample.apply(lambda v: bool(ELAPSED_RE.match(v))).all():
        parts = raw.str.split(":")
        minutes = parts.str[0].astype(float)
        seconds = parts.str[1].astype(float)
        elapsed = minutes * 60 + seconds
        return elapsed.values
    ts = pd.to_datetime(raw, format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
    if ts.isna().mean() > 0.5:
        ts = pd.to_datetime(raw, errors="coerce")
    elapsed = (ts - ts.min()).dt.total_seconds()
    return elapsed.values


def parse_csi(s) -> np.ndarray:

    if not isinstance(s, str):
        return np.array(s, dtype=np.int16)
    s = s.strip().lstrip("[").rstrip("]")
    if not s:
        return np.array([], dtype=np.int16)
    return np.array(s.split(","), dtype=np.int16)


def iq_to_amp_phase(raw: np.ndarray):
    """Raw interleaved [imag, real] int16 pairs -> (amplitude, phase) per subcarrier."""
    pairs = raw.reshape(-1, 2).astype(np.float64)
    imag, real = pairs[:, 0], pairs[:, 1]
    amplitude = np.sqrt(imag ** 2 + real ** 2)
    phase = np.arctan2(imag, real)
    return amplitude, phase


def detect_invalid_subcarriers(amplitude_matrix: np.ndarray, var_ratio_thresh: float = 0.10) -> np.ndarray:
    # 0.02 used to sit right next to known-bad subcarriers' actual ratio (~0.02-0.05),
    # making detection sample-dependent. Real subcarriers measured >=0.30, so 0.10
    # gives wide margin on both sides without risking flagging real signal.

    var = amplitude_matrix.var(axis=0)
    median_var = np.median(var)
    return np.where(var < var_ratio_thresh * median_var)[0]


def hampel_filter_1d(x: np.ndarray, window: int = 7, n_sigma: float = 3.0):
    """Hampel filter: replace outliers (vs rolling median) with the rolling median.

    Returns (cleaned_values, outlier_mask). Operates on a single time-ordered
    1-D series.
    """
    s = pd.Series(x)
    k = 1.4826
    rolling_median = s.rolling(window, center=True, min_periods=1).median()
    abs_dev = (s - rolling_median).abs()
    mad_series = abs_dev.rolling(window, center=True, min_periods=1).median()
    threshold = n_sigma * k * mad_series
    outliers = (abs_dev > threshold) & (mad_series > 0)
    cleaned = s.where(~outliers, rolling_median)
    return cleaned.values, outliers.values


def hampel_filter_columns(matrix: np.ndarray, window: int = 7, n_sigma: float = 3.0) -> np.ndarray:
    """Apply hampel_filter_1d independently down each column (time axis = rows)."""
    out = np.empty_like(matrix, dtype=np.float64)
    for c in range(matrix.shape[1]):
        out[:, c], _ = hampel_filter_1d(matrix[:, c], window=window, n_sigma=n_sigma)
    return out


def sanitize_phase_row(phase_vec: np.ndarray, sc_indices: np.ndarray) -> np.ndarray:

    unwrapped = np.unwrap(phase_vec)
    A = np.vstack([sc_indices, np.ones_like(sc_indices, dtype=np.float64)]).T
    slope, intercept = np.linalg.lstsq(A, unwrapped, rcond=None)[0]
    return unwrapped - (slope * sc_indices + intercept)


def shannon_entropy(values: np.ndarray, bins: int = 16) -> float:
    if values.size == 0:
        return 0.0
    counts, _ = np.histogram(values, bins=bins)
    probs = counts / counts.sum()
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log(probs)))


def mad(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    med = np.median(values)
    return float(np.median(np.abs(values - med)))


FILES = {"0p.csv": 0, "1p.csv": 1, "2p.csv": 2}
RECEIVERS = ["rx1", "rx2", "rx3"]
COMMON_SC = 128         # sender.c now filters to one fixed CSI length (TARGET_CSI_LEN=256
                        # raw bytes = 128 subcarriers), so the old "smallest-common-width"
                        # truncation to 64 is no longer needed for new recordings - use the
                        # full frame. Old mixed-length recordings (128/256/384 raw bytes)
                        # predate this fix and won't all line up with this width: rows with
                        # n_sc < 128 get dropped, rows with n_sc > 128 only use their first
                        # 128 subcarriers (unverified whether that aligns with the new format).
FIRST_WORD_INVALID_SC = (0, 1)   # ESP32 CSI hardware quirk: AGC hasn't settled when the
                                  # first word (first 2 subcarriers) is captured, so these
                                  # are stale/frozen in ~92-96% of frames - always exclude.
WINDOW_SEC = 5.0       # long enough to span >=1 full breathing cycle (~0.2-0.33 Hz)
                       # since presence detection needs to work even when the person
                       # isn't otherwise moving
MIN_SAMPLES_PER_WINDOW = 4
HAMPEL_WINDOW = 7
HAMPEL_NSIGMA = 3.0
FS = 4.0                # uniform resample rate (Hz) for Doppler/STFT analysis
STFT_NPERSEG = 20        # ~5s of context per STFT frame -> 0.2 Hz resolution,
                         # matched to WINDOW_SEC and tuned to land on breathing rate
STFT_HOP = int(WINDOW_SEC * FS)   # stride STFT frames to align with feature windows

# ---------------------------------------------------------------------------
# Step 1: load + clean
# ---------------------------------------------------------------------------

def calibrate_null_subcarriers(files, sample_per_file=4000):
    pooled = []
    for fname in files:
        n = 0
        for chunk in pd.read_csv(fname, usecols=["csi"], chunksize=20000):
            chunk = chunk.dropna(subset=["csi"])
            for s in chunk["csi"]:
                raw = parse_csi(s)
                if raw.size // 2 < COMMON_SC:
                    continue
                amp, _ = iq_to_amp_phase(raw[: COMMON_SC * 2])
                pooled.append(amp)
                n += 1
                if n >= sample_per_file:
                    break
            if n >= sample_per_file:
                break
    mat = np.vstack(pooled)
    search_start = max(FIRST_WORD_INVALID_SC) + 1
    invalid = detect_invalid_subcarriers(mat[:, search_start:]) + search_start  # search excluding first word, then re-offset indices
    invalid = np.union1d(invalid, FIRST_WORD_INVALID_SC)
    print(f"[calibrate] pooled {mat.shape[0]} rows; invalid subcarrier indices (of first {COMMON_SC}): {invalid.tolist()}")
    valid_mask = np.ones(COMMON_SC, dtype=bool)
    valid_mask[invalid] = False
    return valid_mask


def load_and_clean(fname, label, valid_mask):
    """Read a raw CSI CSV from disk and clean it. See clean_dataframe()."""
    df = pd.read_csv(fname, usecols=["esp_id", "timestamp", "rssi", "csi"])
    return clean_dataframe(df, valid_mask, label=label, source_file=fname)


def clean_dataframe(df, valid_mask, label=None, source_file=None):
    """Clean an in-memory CSI DataFrame (esp_id/timestamp/rssi/csi columns).

    Shared by file-based training/batch ingestion (load_and_clean) and
    live buffer-based inference, which has no file path or label.
    """
    df = df.dropna(subset=["esp_id", "timestamp", "csi"])
    df["t"] = parse_timestamps(df["timestamp"])
    df = df.dropna(subset=["t"])

    n_valid = int(valid_mask.sum())
    sc_indices = np.arange(COMMON_SC)[valid_mask]

    rows = []
    keep = []
    for s in df["csi"]:
        raw = parse_csi(s)
        if raw.size < 2 or raw.size % 2 != 0:
            # Truncated/corrupted capture (odd IQ count) - can't pair into
            # (imag, real) samples, drop the row rather than crash.
            keep.append(False)
            continue
        n_sc = raw.size // 2
        if n_sc < COMMON_SC:
            # Frame narrower than the calibrated width (legacy/truncated PHY
            # format) can't be aligned to valid_mask - drop the row outright
            # rather than NaN-padding it. With the new fixed-length firmware
            # every frame is exactly COMMON_SC wide, so this only ever skips
            # leftover old-format rows.
            keep.append(False)
            continue
        amp_full, _ = iq_to_amp_phase(raw)
        full_mask = np.ones(n_sc, dtype=bool)
        full_mask[:COMMON_SC] = valid_mask
        amp_full = amp_full[full_mask]
        amp_c, phase_c = iq_to_amp_phase(raw[: COMMON_SC * 2])
        amp_c, phase_c = amp_c[valid_mask], phase_c[valid_mask]
        phase_c = sanitize_phase_row(phase_c, sc_indices)
        rows.append((amp_full, amp_c, phase_c, n_sc))
        keep.append(True)

    df = df[keep].reset_index(drop=True)
    df["amp_full"] = [r[0] for r in rows]
    df["amp_common"] = [r[1] for r in rows]
    df["phase_common"] = [r[2] for r in rows]
    df["n_sc"] = [r[3] for r in rows]
    if label is not None:
        df["label"] = label
    if source_file is not None:
        df["source_file"] = source_file

    df = df.dropna(subset=["amp_common"]).reset_index(drop=True)
    df = df[df["amp_common"].apply(lambda a: not np.isnan(a).any())].reset_index(drop=True)

    # Row-level Hampel glitch rejection + per-subcarrier-column smoothing,
    # applied per receiver in chronological order.
    cleaned_chunks = []
    for esp_id, grp in df.groupby("esp_id", sort=False):
        grp = grp.sort_values("t").reset_index(drop=True)
        common_mat = np.vstack(grp["amp_common"].values)
        row_mean = common_mat.mean(axis=1)
        _, glitch_mask = hampel_filter_1d(row_mean, window=HAMPEL_WINDOW, n_sigma=HAMPEL_NSIGMA)
        grp = grp[~glitch_mask].reset_index(drop=True)
        common_mat = np.vstack(grp["amp_common"].values)
        smoothed = hampel_filter_columns(common_mat, window=HAMPEL_WINDOW, n_sigma=HAMPEL_NSIGMA)
        grp["amp_common"] = list(smoothed)
        cleaned_chunks.append(grp)

    return pd.concat(cleaned_chunks, ignore_index=True), sc_indices


# ---------------------------------------------------------------------------
# Step 2: feature engineering
# ---------------------------------------------------------------------------

def spectral_entropy(p):
    p = p[p > 0]
    if p.size == 0:
        return 0.0
    return float(-np.sum(p * np.log(p)))


def precompute_stft(grp, t0):
    grp = grp.sort_values("t")
    t = grp["t"].values
    amp_mean = np.vstack(grp["amp_common"].values).mean(axis=1)
    t_grid = np.arange(t0, t.max(), 1.0 / FS)
    amp_grid = np.interp(t_grid, t, amp_mean)
    noverlap = STFT_NPERSEG - STFT_HOP
    f, t_stft, Zxx = stft(amp_grid, fs=FS, nperseg=min(STFT_NPERSEG, len(amp_grid)),
                           noverlap=min(noverlap, max(len(amp_grid) - 1, 0)))
    return t_stft + t0, f, np.abs(Zxx), t_grid, amp_grid


def doppler_features_at(window_center, t_stft, freqs, mag):
    if len(t_stft) == 0:
        return 0.0, 0.0, 0.0
    idx = np.argmin(np.abs(t_stft - window_center))
    spectrum = mag[:, idx]
    ac = spectrum[1:]  # exclude DC bin
    if ac.sum() <= 0:
        return 0.0, 0.0, 0.0
    dom_freq = float(freqs[1:][np.argmax(ac)])
    energy = float(np.sum(ac ** 2))
    p = ac / ac.sum()
    return dom_freq, energy, spectral_entropy(p)


def cross_rx_amp_features(wc, stft_cache, context_sec=2 * WINDOW_SEC):

    lo, hi = wc - context_sec / 2, wc + context_sec / 2
    slices = {}
    for rx in RECEIVERS:
        t_grid, amp_grid = stft_cache[rx][3], stft_cache[rx][4]
        mask = (t_grid >= lo) & (t_grid < hi)
        slices[rx] = amp_grid[mask]

    feat = {}
    for a, b in (("rx1", "rx2"), ("rx1", "rx3"), ("rx2", "rx3")):
        sa, sb = slices[a], slices[b]
        n = min(len(sa), len(sb))
        corr, diff = 0.0, 0.0
        if n >= 2:
            sa, sb = sa[:n], sb[:n]
            diff = float(np.mean(sa - sb))
            if np.std(sa) > 0 and np.std(sb) > 0:
                corr = float(np.corrcoef(sa, sb)[0, 1])
        feat[f"{a}_{b}_amp_corr"] = corr
        feat[f"{a}_{b}_amp_diff"] = diff
    return feat


def build_windows(df, label=None):
    t_max = df["t"].max()
    edges = np.arange(0, t_max + WINDOW_SEC, WINDOW_SEC)

    by_rx = {rx: grp for rx, grp in df.groupby("esp_id")}
    t0 = df["t"].min()
    stft_cache = {rx: precompute_stft(grp, t0) for rx, grp in by_rx.items() if rx in RECEIVERS}

    records = []
    for i in range(len(edges) - 1):
        ws, we = edges[i], edges[i + 1]
        wc = ws + WINDOW_SEC / 2
        feat = {"window_start_t": ws}
        if label is not None:
            feat["label"] = label
        valid = True
        for rx in RECEIVERS:
            grp = by_rx.get(rx)
            if grp is None:
                valid = False
                break
            sub = grp[(grp["t"] >= ws) & (grp["t"] < we)]
            if len(sub) < MIN_SAMPLES_PER_WINDOW:
                valid = False
                break

            amp_full_pool = np.concatenate(sub["amp_full"].values)
            feat[f"{rx}_amp_var"] = float(np.var(amp_full_pool))
            feat[f"{rx}_amp_std"] = float(np.std(amp_full_pool))
            feat[f"{rx}_amp_entropy"] = shannon_entropy(amp_full_pool)
            feat[f"{rx}_amp_mad"] = mad(amp_full_pool)
            feat[f"{rx}_mean_sc_count"] = float(sub["n_sc"].mean())  # diagnostic only, see report

            # Pool across time AND subcarrier (not mean-reduced first): the
            # linear detrend in sanitize_phase_row makes each row's mean
            # residual ~0 by construction (OLS residuals sum to zero), so
            # averaging across subcarriers per row would erase the signal.
            phase_pool = np.concatenate(sub["phase_common"].values)
            feat[f"{rx}_phase_std"] = float(np.std(phase_pool))
            feat[f"{rx}_phase_mad"] = mad(phase_pool)

            common_mat = np.vstack(sub["amp_common"].values)
            n_comp = min(3, common_mat.shape[0] - 1, common_mat.shape[1])
            if n_comp >= 1:
                from sklearn.decomposition import PCA
                pca = PCA(n_components=n_comp)
                pca.fit(common_mat)
                ev = list(pca.explained_variance_) + [0.0] * (3 - n_comp)
            else:
                ev = [0.0, 0.0, 0.0]
            feat[f"{rx}_pc1_var"], feat[f"{rx}_pc2_var"], feat[f"{rx}_pc3_var"] = ev[:3]

            t_stft, freqs, mag = stft_cache[rx][0], stft_cache[rx][1], stft_cache[rx][2]
            dom_freq, energy, sentropy = doppler_features_at(wc, t_stft, freqs, mag)
            feat[f"{rx}_doppler_freq"] = dom_freq
            feat[f"{rx}_doppler_energy"] = energy
            feat[f"{rx}_doppler_entropy"] = sentropy

        if valid:
            feat.update(cross_rx_amp_features(wc, stft_cache))
            records.append(feat)

    return pd.DataFrame.from_records(records)


# ---------------------------------------------------------------------------
# Step 3: per-session baseline normalization
#
# CSI feature magnitudes (amp_var, doppler_energy, ...) depend heavily on the
# specific room/antenna/channel of a given recording session, not just on how
# many people are present. A model trained on raw magnitudes learns "this
# session's empty room looks like X" and fails on any new session - which is
# exactly the "always predicts 0 in deployment" symptom.
#
# Fix: every session starts with an empty-room (0-person) capture. We take the
# mean feature vector of those empty windows as that session's baseline, and
# subtract it from every window in the session, so features express *deviation
# from this room's empty channel* instead of absolute magnitude. At deployment
# the same is done from a one-time empty-room calibration capture.
# ---------------------------------------------------------------------------

# Columns produced by build_windows()/processing that are metadata, never
# model features and never normalized.
META_COLS = ("window_start_t", "label", "session_id", "source_file")


def feature_columns_of(df):
    """Model-feature column names of a build_windows() frame (excludes metadata)."""
    return [c for c in df.columns if c not in META_COLS]


def compute_baseline(empty_windows: pd.DataFrame) -> pd.Series:
    """Per-feature mean over empty-room (0-person) windows = a session's
    'empty channel' fingerprint. Returned as a Series indexed by feature name
    so it can be subtracted from any window frame by label alignment."""
    cols = feature_columns_of(empty_windows)
    return empty_windows[cols].mean()


def apply_baseline(windows: pd.DataFrame, baseline: pd.Series) -> pd.DataFrame:
    """Subtract a session/deployment baseline from every window so features
    express deviation from the empty room. Metadata columns pass through
    untouched; features absent from the baseline are left as-is."""
    out = windows.copy()
    cols = [c for c in feature_columns_of(out) if c in baseline.index]
    out[cols] = out[cols].sub(baseline[cols], axis=1)
    return out


