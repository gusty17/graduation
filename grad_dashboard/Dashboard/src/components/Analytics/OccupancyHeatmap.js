import React from "react";
import { View, Text } from "react-native";
import styles from "./styles";

export default function OccupancyHeatmap({ predictions }) {
  if (!predictions.length) return null;

  return (
    <View style={styles.grid}>
      {predictions.map((p, i) => {
        const intensity = Math.min(p.person_count / 3, 1);

        return (
          <View
            key={i}
            style={[
              styles.cell,
              { backgroundColor: `rgba(0,255,255,${intensity})` },
            ]}
          >
            <Text style={styles.cellText}>{p.person_count}</Text>
          </View>
        );
      })}
    </View>
  );
}
