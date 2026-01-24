import React from "react";
import { ScrollView, View } from "react-native";
import { useNavigation } from "@react-navigation/native";

import { useWiFiCSIContext } from "../../context/WiFiCSIContext";

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

  return (
    <ScrollView style={styles.container}>
      <Header />

      <StatusCard
        icon="🎯"
        title="DETECTION STATUS"
        value={wifi.detectionStatus}
      />

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
              onAnalyze={wifi.processFile}
              onClear={wifi.clearFile}
              onAnalytics={() => navigation.navigate("Analytics")}
            />
          </View>
        </View>

        {/* RIGHT PANEL */}
        <View style={styles.rightColumn}>
          <View style={styles.rightPanel}>
            <TimestampSelector
              timestamps={wifi.timestamps}
              value={wifi.selectedTimestamp}
              onChange={wifi.setSelectedTimestamp}
            />

            <PlayButton
              isPlaying={wifi.isPlaying}
              onPress={wifi.togglePlay}
            />

            {wifi.predictions.length >= 0 && (
              <DetectionResults
                confidence={wifi.confidence}
                activePerson={wifi.activePerson}
              />
            )}
          </View>
        </View>
      </View>
    </ScrollView>
  );
}
