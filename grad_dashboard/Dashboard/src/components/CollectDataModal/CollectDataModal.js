import React, { useEffect, useMemo, useState } from "react";
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from "react-native";

import useCollection from "../../hooks/useCollection";
import colors from "../../styles/colors";
import styles from "./styles";

const RECEIVERS = ["rx1", "rx2", "rx3"];

const fmt = (secs) => {
  const s = Math.max(0, Math.round(secs || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

export default function CollectDataModal({ visible, onClose }) {
  const { status, sessions, error, start, stop } = useCollection(visible);

  const [label, setLabel] = useState("0p");
  const [sessionName, setSessionName] = useState("");
  const [minutes, setMinutes] = useState("10");
  const [recordAnother, setRecordAnother] = useState(false);

  const recording = status?.active;
  const summary = status?.summary;
  const view = recording ? "recording" : summary && !recordAnother ? "summary" : "setup";

  // Prefill the session name with the backend's suggestion while idle.
  useEffect(() => {
    if (visible && !recording && sessions?.suggested && !sessionName) {
      setSessionName(sessions.suggested);
    }
  }, [visible, recording, sessions, sessionName]);

  // Reset transient UI each time the modal opens.
  useEffect(() => {
    if (visible) setRecordAnother(false);
  }, [visible]);

  const labelExists = useMemo(() => {
    const s = (sessions?.sessions || []).find((x) => x.session === sessionName);
    return s ? s.labels.includes(label) : false;
  }, [sessions, sessionName, label]);

  const onStart = async () => {
    const dur = Math.round((parseFloat(minutes) || 0) * 60);
    const ok = await start({ label, session: sessionName.trim(), duration: dur });
    if (ok) setRecordAnother(false);
  };

  const counts = status?.counts || {};

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <View style={styles.headerRow}>
            <Text style={styles.title}>🧪 COLLECT TRAINING DATA</Text>
            {!recording && (
              <TouchableOpacity onPress={onClose}>
                <Text style={styles.close}>✕</Text>
              </TouchableOpacity>
            )}
          </View>

          {error ? <Text style={styles.error}>⚠ {error}</Text> : null}

          {/* ───────────── SETUP ───────────── */}
          {view === "setup" && (
            <ScrollView style={{ maxHeight: 460 }}>
              <Text style={styles.hint}>
                Keep the room in the chosen state (0 / 1 / 2 people) for the whole
                recording. The live prediction pipeline is paused while collecting.
              </Text>

              <Text style={styles.fieldLabel}>PEOPLE IN ROOM</Text>
              <View style={styles.labelRow}>
                {(sessions?.labels || ["0p", "1p", "2p"]).map((lb) => (
                  <TouchableOpacity
                    key={lb}
                    style={[styles.chip, label === lb && styles.chipActive]}
                    onPress={() => setLabel(lb)}
                  >
                    <Text style={[styles.chipText, label === lb && styles.chipTextActive]}>
                      {lb.replace("p", " person" + (lb === "1p" ? "" : "s")).replace("0 persons", "empty")}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.fieldLabel}>SESSION FOLDER</Text>
              <TextInput
                style={styles.input}
                value={sessionName}
                onChangeText={setSessionName}
                placeholder="session_03"
                placeholderTextColor={colors.textSubtle}
                autoCapitalize="none"
              />
              {labelExists ? (
                <Text style={styles.warn}>
                  ⚠ {sessionName}/{label}.csv already exists — starting will overwrite it.
                </Text>
              ) : null}

              <Text style={styles.fieldLabel}>DURATION (MINUTES)</Text>
              <TextInput
                style={styles.input}
                value={minutes}
                onChangeText={setMinutes}
                keyboardType="numeric"
                placeholder="10"
                placeholderTextColor={colors.textSubtle}
              />

              {sessions?.sessions?.length ? (
                <Text style={styles.existing}>
                  Existing:{" "}
                  {sessions.sessions
                    .map((s) => `${s.session} [${s.labels.join(",") || "—"}]`)
                    .join("   ")}
                </Text>
              ) : null}

              <TouchableOpacity
                style={[styles.primaryBtn, !sessionName.trim() && { opacity: 0.4 }]}
                disabled={!sessionName.trim()}
                onPress={onStart}
              >
                <Text style={styles.primaryBtnText}>● START RECORDING</Text>
              </TouchableOpacity>
            </ScrollView>
          )}

          {/* ───────────── RECORDING ───────────── */}
          {view === "recording" && (
            <View>
              <Text style={styles.recTitle}>
                ● Recording {status.label} → {status.session}
              </Text>
              <Text style={styles.countdown}>{fmt(status.remaining)}</Text>
              <Text style={styles.hint}>time remaining (auto-saves at 0)</Text>

              <View style={styles.rxRow}>
                {RECEIVERS.map((rx) => {
                  const n = counts[rx] || 0;
                  return (
                    <View key={rx} style={styles.rxBox}>
                      <Text style={styles.rxName}>{rx.toUpperCase()}</Text>
                      <Text style={[styles.rxCount, { color: n > 0 ? colors.lime : "#d9534f" }]}>
                        {n}
                      </Text>
                      <Text style={styles.rxState}>{n > 0 ? "receiving" : "no data"}</Text>
                    </View>
                  );
                })}
              </View>

              {RECEIVERS.some((rx) => (counts[rx] || 0) === 0) ? (
                <Text style={styles.warn}>
                  ⚠ A receiver has 0 rows — check it's powered/connected before the timer ends.
                </Text>
              ) : null}
              {counts.dropped_len ? (
                <Text style={styles.hint}>dropped (wrong CSI length): {counts.dropped_len}</Text>
              ) : null}

              <TouchableOpacity style={styles.stopBtn} onPress={stop}>
                <Text style={styles.stopBtnText}>■ STOP &amp; SAVE NOW</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* ───────────── SUMMARY ───────────── */}
          {view === "summary" && (
            <View>
              <Text style={[styles.recTitle, { color: summary.ok ? colors.lime : "#d9534f" }]}>
                {summary.ok ? "✅ Saved" : "⚠ Saved with a weak receiver"}
              </Text>
              <Text style={styles.summaryLine}>
                {summary.session}/{summary.label}.csv — {summary.rows} rows
              </Text>
              <View style={styles.rxRow}>
                {RECEIVERS.map((rx) => (
                  <View key={rx} style={styles.rxBox}>
                    <Text style={styles.rxName}>{rx.toUpperCase()}</Text>
                    <Text
                      style={[
                        styles.rxCount,
                        { color: (summary.counts[rx] || 0) > 0 ? colors.lime : "#d9534f" },
                      ]}
                    >
                      {summary.counts[rx] || 0}
                    </Text>
                  </View>
                ))}
              </View>
              {!summary.ok ? (
                <Text style={styles.warn}>
                  Weakest receiver captured 0 rows — re-record this segment.
                </Text>
              ) : null}

              <View style={styles.summaryBtnRow}>
                <TouchableOpacity
                  style={[styles.primaryBtn, { flex: 1 }]}
                  onPress={() => setRecordAnother(true)}
                >
                  <Text style={styles.primaryBtnText}>+ RECORD ANOTHER</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.ghostBtn, { flex: 1 }]} onPress={onClose}>
                  <Text style={styles.ghostBtnText}>DONE</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}
