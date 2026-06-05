import { View, Text } from 'react-native';
import styles from "./styles";

export default function StatusCard({ icon, title, value }) {
  return (
    <View style={styles.statusCard}>
      <Text style={styles.statusIcon}>{icon}</Text>
      <View>
        <Text style={styles.statusTitle}>{title}</Text>
        <Text style={styles.statusValue}>{value}</Text>
      </View>
    </View>
  );
}
