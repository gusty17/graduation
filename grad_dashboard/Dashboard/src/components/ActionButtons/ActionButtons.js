import React from "react";
import { View, TouchableOpacity, Text } from "react-native";
import { useNavigation } from "@react-navigation/native";
import styles from "./styles";

export default function ActionButtons({ onAnalyze, onClear }) {
  const navigation = useNavigation();

  return (
    <View style={styles.actionCard}>
      <TouchableOpacity style={styles.analyzeButton} onPress={onAnalyze}>
        <Text style={styles.analyzeButtonText}>🚀 ANALYZE DATA</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.clearButton} onPress={onClear}>
        <Text style={styles.clearButtonText}>✖ CLEAR</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.analyticsButton}
        onPress={() => navigation.navigate("Analytics")}
      >
        <Text style={styles.analyticsButtonText}>📊 VIEW ANALYTICS</Text>
      </TouchableOpacity>
    </View>
  );
}
