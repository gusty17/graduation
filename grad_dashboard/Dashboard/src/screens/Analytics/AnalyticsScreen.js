import React, { useEffect, useMemo, useState } from "react";
import {
  ScrollView,
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useNavigation } from "@react-navigation/native";

import { fetchAnalytics } from "../../api/api";

import OccupancyChart from "../../components/Analytics/OccupancyChart";
import OccupancyTable from "../../components/Analytics/OccupancyTable";
import OccupancyStats from "../../components/Analytics/OccupancyStats";

import styles from "./styles";

/* ---------- HELPERS ---------- */
const onePerSecond = (predictions) => {
  const seen = new Set();
  return predictions.filter((p) => {
    const sec = p.timestamp.slice(0, 19);
    if (seen.has(sec)) return false;
    seen.add(sec);
    return true;
  });
};

const groupByDay = (predictions) => {
  return predictions.reduce((acc, p) => {
    const day = p.timestamp.slice(0, 10); // YYYY-MM-DD
    if (!acc[day]) acc[day] = [];
    acc[day].push(p);
    return acc;
  }, {});
};

export default function AnalyticsScreen() {
  const navigation = useNavigation();

  const [rawData, setRawData] = useState([]);
  const [dayIndex, setDayIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  /* ================= FETCH ALL FILES ================= */
  useEffect(() => {
    fetchAnalytics()
      .then(setRawData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  /* ================= MERGE ALL FILES ================= */
  const allPredictions = useMemo(() => {
    const merged = [];

    rawData.forEach((file) => {
      Object.values(file.days).forEach((dayArray) => {
        merged.push(...dayArray);
      });
    });

    return merged;
  }, [rawData]);

  /* ================= GROUP BY DAY ================= */
  const groupedByDay = useMemo(
    () => groupByDay(onePerSecond(allPredictions)),
    [allPredictions]
  );

  const days = Object.keys(groupedByDay);

  const dayData = days.length
    ? groupedByDay[days[dayIndex]]
    : [];

  const chartData = dayData.map((p) => ({
    timestamp: p.timestamp.slice(11, 19),
    persons: p.person_count,
  }));

  /* ================= STATES ================= */
  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#00ffff" />
      </View>
    );
  }

  if (!days.length) {
    return (
      <View style={styles.container}>
        {/* BACK BUTTON */}
        <TouchableOpacity
          onPress={() => navigation.navigate("Dashboard")}
          style={styles.backButton}
        >
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>

        <Text style={styles.title}>No analytics data</Text>
      </View>
    );
  }

  const canPrev = dayIndex > 0;
  const canNext = dayIndex < days.length - 1;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: 60 }}
    >
      {/* BACK BUTTON */}
      <TouchableOpacity
        onPress={() => navigation.navigate("Dashboard")}
        style={styles.backButton}
      >
        <Text style={styles.backButtonText}>Back</Text>
      </TouchableOpacity>

      <Text style={styles.title}>ANALYTICS</Text>
      <Text style={styles.dayLabel}>{days[dayIndex]}</Text>

      {/* ===== STATS + TABLE ===== */}
      <View style={styles.statsTableBox}>
        {/* LEFT ARROW */}
        <TouchableOpacity
          disabled={!canPrev}
          onPress={() => canPrev && setDayIndex(dayIndex - 1)}
          style={[
            styles.leftArrow,
            !canPrev && styles.arrowDisabled,
          ]}
        >
          <Text style={styles.arrowText}>❮</Text>
        </TouchableOpacity>

        {/* RIGHT ARROW */}
        <TouchableOpacity
          disabled={!canNext}
          onPress={() => canNext && setDayIndex(dayIndex + 1)}
          style={[
            styles.rightArrow,
            !canNext && styles.arrowDisabled,
          ]}
        >
          <Text style={styles.arrowText}>❯</Text>
        </TouchableOpacity>

        <View style={styles.topRow}>
          <View style={styles.statsCol}>
            <OccupancyStats predictions={dayData} />
          </View>

          <View style={styles.tableCol}>
            <OccupancyTable predictions={dayData} />
          </View>
        </View>
      </View>

      {/* ===== CHART ===== */}
      <View style={styles.chartSection}>
        <Text style={styles.sectionTitle}>
          Occupancy Over Time
        </Text>
        <OccupancyChart data={chartData} />
      </View>
    </ScrollView>
  );
}
