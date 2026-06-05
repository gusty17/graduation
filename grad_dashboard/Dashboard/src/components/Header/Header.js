import { View, Text } from 'react-native';
import styles from './styles';

export default function Header() {
  return (
    <View style={styles.headerCard}>
      <Text style={styles.headerIcon}>⚡</Text>
      <View>
        <Text style={styles.headerTitle}>WiFi CSI TRACKING</Text>
        <Text style={styles.headerSubtitle}>
          Occupancy Detection & Monitoring
        </Text>
      </View>
    </View>
  );
}
