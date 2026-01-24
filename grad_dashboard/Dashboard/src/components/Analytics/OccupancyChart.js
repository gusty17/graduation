import React from "react";
import { View } from "react-native";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function OccupancyChart({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <View style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis
            dataKey="timestamp"
            tick={{ fill: "#00ff88", fontSize: 10 }}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "#00ff88" }}
          />
          <Tooltip />
          <Line
            type="stepAfter"
            dataKey="persons"
            stroke="#00ffff"
            strokeWidth={3}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </View>
  );
}
