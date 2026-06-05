import React, { useRef } from "react";
import { View, Text, TouchableOpacity, Platform } from "react-native";
import styles from "./styles";

export default function FileUploadCard({ file, onSelect }) {
  const fileInputRef = useRef(null);

  const handleWebUpload = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    console.log("📁 Web file selected:", selectedFile);
    onSelect(selectedFile);
  };

  const openFileDialog = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <View style={styles.uploadCard}>
      {/* HEADER */}
      <View style={styles.uploadHeader}>
        <Text style={styles.uploadHeaderIcon}>📡</Text>
        <Text style={styles.uploadHeaderText}>DATA UPLOAD</Text>
      </View>

      <View style={styles.uploadDivider} />

      {/* SYSTEM READY */}
      <View style={styles.systemReady}>
        <View style={styles.greenDot} />
        <Text style={styles.systemReadyText}>SYSTEM READY</Text>
      </View>

      {/* UPLOAD ZONE */}
      <View style={styles.uploadZone}>
        <Text style={styles.uploadIcon}>📊</Text>
        <Text style={styles.uploadTitle}>Upload CSI Data File</Text>
        <Text style={styles.uploadSubtitle}>Tap to select CSV file</Text>

        {/* Hidden input (WEB ONLY) */}
        {Platform.OS === "web" && (
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleWebUpload}
            style={{ display: "none" }}
          />
        )}

        <TouchableOpacity style={styles.selectBtn} onPress={openFileDialog}>
          <Text style={styles.selectBtnText}>SELECT FILE</Text>
        </TouchableOpacity>
      </View>

      {/* FILE NAME */}
      {file && <Text style={styles.fileName}>{file.name}</Text>}
    </View>
  );
}
