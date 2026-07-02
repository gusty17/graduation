import React, { useState, useEffect } from "react";
import { ScrollView, View, TouchableOpacity, Text } from "react-native";
import { useNavigation } from "@react-navigation/native";

import { useWiFiCSIContext } from "../../context/WiFiCSIContext";
import useLiveSSE from "../../hooks/useLiveSSE";
import useCalibrationStatus from "../../hooks/useCalibrationStatus";

const formatTime = (secs) => {
  const s = Math.max(0, Math.round(secs || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
};

import Header from "../../components/Header/Header";
import StatusCard from "../../components/StatusCard/StatusCard";
import FileUploadCard from "../../components/FileUploadCard/FileUploadCard";
import TimestampSelector from "../../components/TimestampSelector/TimestampSelector";
import DetectionResults from "../../components/DetectionResults/DetectionResults";
import ActionButtons from "../../components/ActionButtons/ActionButtons";
import PlayButton from "../../components/PlayButton/PlayButton";
import CollectDataModal from "../../components/CollectDataModal/CollectDataModal";

import styles from "./styles";

export default function DashboardScreen() {
  const wifi = useWiFiCSIContext();
  const navigation = useNavigation();

  const [isLive, setIsLive] = useState(false);
  const [showCollect, setShowCollect] = useState(false);
  const [analyzeClicked, setAnalyzeClicked] = useState(false);
  const liveData = useLiveSSE(isLive);
  const calib = useCalibrationStatus(isLive);
  const isCalibrating = isLive && calib?.phase === "calibrating";

  const handleAnalyze = () => {
    setAnalyzeClicked(true);
    wifi.processFile();
  };

  // Reset file when  live prediction
  useEffect(() => {
    if (isLive) {
      // Only clear file when transitioning FROM non-live TO live
      wifi.clearFile();
      setAnalyzeClicked(false);
    }
  }, [isLive]);

  return (
    <ScrollView style={styles.container}>
      <Header />

      {/* TRAINING-DATA COLLECTION — opens the guided recording modal */}
      <TouchableOpacity
        style={{
          backgroundColor: "rgba(0,255,255,0.12)",
          borderWidth: 1.5,
          borderColor: "#00ffff",
          borderRadius: 12,
          paddingVertical: 12,
          alignItems: "center",
          marginBottom: 15,
        }}
        onPress={() => setShowCollect(true)}
      >
        <Text style={{ color: "#00ffff", fontWeight: "bold", letterSpacing: 2 }}>
          🧪 COLLECT TRAINING DATA
        </Text>
      </TouchableOpacity>

      <StatusCard
        icon="🎯"
        title="DETECTION STATUS"
        value={isLive ? (isCalibrating ? "CALIBRATING" : "LIVE MODE") : wifi.detectionStatus}
      />

      {/* CALIBRATION PHASE — empty-room baseline measurement on startup */}
      {isCalibrating && (
        <StatusCard
          icon="🧪"
          title="CALIBRATION — KEEP ROOM EMPTY"
          value={`Measuring empty room… ${formatTime(calib.remaining)} remaining`}
        />
      )}

      {/* LIVE STATUS — only after calibration finishes */}
      {isLive && !isCalibrating && (
        <StatusCard
          icon="👥"
          title="REAL-TIME OCCUPANCY"
          value={
            liveData
              ? `${liveData.person_count} person(s) • ${liveData.confidence}%`
              : "Waiting for data..."
          }
        />
      )}

      <View style={styles.mainRow}>
        {/* LEFT PANEL */}
        <View style={styles.leftColumn}>
          <View style={styles.leftPanel}>
            <View style={styles.uploadContent}>
              <FileUploadCard
                file={wifi.currentFile}
                onSelect={wifi.handleFileSelect}
              />
            </View>

            <ActionButtons
              onAnalyze={handleAnalyze}
              onClear={wifi.clearFile}
              onToggleLive={() => setIsLive((p) => !p)}
              isLive={isLive}
            />
          </View>
        </View>

        {/* RIGHT PANEL */}
        <View style={styles.rightColumn}>
          <View style={styles.rightPanel}>
            {!isLive && wifi.currentFile && (
              <>
                <TimestampSelector
                  timestamps={wifi.timestamps}
                  value={wifi.selectedTimestamp}
                  onChange={wifi.setSelectedTimestamp}
                  disabled={!wifi.currentFile}
                />

                <PlayButton
                  isPlaying={wifi.isPlaying}
                  onPress={wifi.togglePlay}
                  disabled={!wifi.currentFile}
                />
              </>
            )}

            {/* ALWAYS RENDER */}
            <DetectionResults
              confidence={isLive ? liveData?.confidence : wifi.confidence}
              activePerson={
                isLive ? liveData?.person_count : wifi.activePerson
              }
              isLive={isLive}
            />
          </View>
        </View>
      </View>

      <CollectDataModal
        visible={showCollect}
        onClose={() => setShowCollect(false)}
      />
    </ScrollView>
  );
}
