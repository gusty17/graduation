import React from "react";
import { View, TouchableOpacity, Text } from "react-native";
import { useNavigation } from "@react-navigation/native";
import styles from "./styles";

export default function ActionButtons({
  onAnalyze,
  onClear,
  onToggleLive,
  isLive,
}) {
  const navigation = useNavigation();

  return (
    <View style={styles.actionCard}>
      {/* ANALYZE CSV */}
      <TouchableOpacity
        style={[
          styles.analyzeButton,
          isLive && { opacity: 0.4 }
        ]}
        disabled={isLive}
        onPress={onAnalyze}
      >
        <Text style={styles.analyzeButtonText}>🚀 ANALYZE DATA</Text>
      </TouchableOpacity>

      {/* LIVE TOGGLE */}
      <TouchableOpacity
        style={[
          styles.analyzeButton,
          {
            backgroundColor: isLive ? "#d9534f" : "#5cb85c",
            marginTop: 10,
          },
        ]}
        onPress={onToggleLive}
      >
        <Text style={styles.analyzeButtonText}>
          {isLive ? "⛔ STOP LIVE PREDICTION" : "▶ START LIVE PREDICTION"}
        </Text>
      </TouchableOpacity>

      {/* CLEAR */}
      <TouchableOpacity style={styles.clearButton} onPress={onClear}>
        <Text style={styles.clearButtonText}>✖ CLEAR</Text>
      </TouchableOpacity>

      {/* ANALYTICS */}
      <TouchableOpacity
        style={styles.analyticsButton}
        onPress={() => navigation.navigate("Analytics")}
      >
        <Text style={styles.analyticsButtonText}>📊 VIEW ANALYTICS</Text>
      </TouchableOpacity>
    </View>
  );
}
