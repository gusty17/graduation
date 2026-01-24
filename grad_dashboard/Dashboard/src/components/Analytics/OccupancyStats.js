import React from "react";
import { View, Text } from "react-native";
import styles from "./styles";

export default function OccupancyStats({ predictions }) {
  if (!predictions.length) return null;

  const counts = predictions.map(p => p.person_count);

  const mean =
    (counts.reduce((a, b) => a + b, 0) / counts.length).toFixed(2);

  const max = Math.max(...counts);
  const min = Math.min(...counts);

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>SUMMARY STATISTICS</Text>

      <View style={styles.row}>
        <Text style={styles.label}>Average Occupancy</Text>
        <Text style={styles.value}>{mean}</Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.label}>Maximum Occupancy</Text>
        <Text style={styles.value}>{max}</Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.label}>Minimum Occupancy</Text>
        <Text style={styles.value}>{min}</Text>
      </View>
    </View>
  );
}
