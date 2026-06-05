import React from "react";
import { View, Text, ScrollView } from "react-native";
import styles from "./styles";

export default function OccupancyTable({ predictions }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>TIMESTAMP OCCUPANCY</Text>

      <View style={styles.tableHeader}>
        <Text style={styles.tableHeaderText}>Time</Text>
        <Text style={styles.tableHeaderText}>Persons</Text>
      </View>

      <ScrollView style={{ maxHeight: 260 }}>
        {predictions.map((p, i) => (
          <View key={i} style={styles.tableRow}>
            <Text style={styles.tableCellLeft}>
              {p.timestamp.slice(11, 19)}
            </Text>
            <Text style={styles.tableCellRight}>
              {p.person_count}
            </Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}
