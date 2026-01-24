import { View, Text } from 'react-native';
import Slider from '@react-native-community/slider';
import styles from './styles';

export default function TimestampSelector({ timestamps, value, onChange }) {
  if (!timestamps.length) return null;

  const progress =
    (value / Math.max(timestamps.length - 1, 1)) * 100;

  return (
    <View style={styles.timestampCard}>
      <View style={styles.timestampHeader}>
        <Text style={styles.timestampLabel}>SELECT TIMESTAMP</Text>
        <View style={styles.timestampBadge}>
          <Text style={styles.timestampBadgeText}>
            {timestamps[value]}
          </Text>
        </View>
      </View>

      {/* Track background */}
      <View style={styles.sliderTrack}>
        <View
          style={[
            styles.sliderFill,
            { width: `${progress}%` },
          ]}
        />
      </View>

      <Slider
        style={styles.slider}
        minimumValue={0}
        maximumValue={timestamps.length - 1}
        value={value}
        onValueChange={(v) => onChange(Math.round(v))}
        minimumTrackTintColor="transparent"
        maximumTrackTintColor="transparent"
        thumbTintColor="#00ffff"
      />

      <View style={styles.timestampMarks}>
        <Text style={styles.timestampMark}>{timestamps[0]}</Text>
        <Text style={styles.timestampMark}>
          {timestamps[Math.floor(timestamps.length / 2)]}
        </Text>
        <Text style={styles.timestampMark}>
          {timestamps[timestamps.length - 1]}
        </Text>
      </View>
    </View>
  );
}
