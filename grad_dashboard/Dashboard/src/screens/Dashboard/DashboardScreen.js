import React, { useState, useEffect } from "react";
import { ScrollView, View } from "react-native";
import { useNavigation } from "@react-navigation/native";

import { useWiFiCSIContext } from "../../context/WiFiCSIContext";
import useLiveSSE from "../../hooks/useLiveSSE";

import Header from "../../components/Header/Header";
import StatusCard from "../../components/StatusCard/StatusCard";
import FileUploadCard from "../../components/FileUploadCard/FileUploadCard";
import TimestampSelector from "../../components/TimestampSelector/TimestampSelector";
import DetectionResults from "../../components/DetectionResults/DetectionResults";
import ActionButtons from "../../components/ActionButtons/ActionButtons";
import PlayButton from "../../components/PlayButton/PlayButton";

import styles from "./styles";

export default function DashboardScreen() {
  const wifi = useWiFiCSIContext();
  const navigation = useNavigation();

  const [isLive, setIsLive] = useState(false);
  const [analyzeClicked, setAnalyzeClicked] = useState(false);
  const liveData = useLiveSSE(isLive);

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

      <StatusCard
        icon="🎯"
        title="DETECTION STATUS"
        value={isLive ? "LIVE MODE" : wifi.detectionStatus}
      />

      {/* LIVE STATUS */}
      {isLive && (
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
    </ScrollView>
  );
}
