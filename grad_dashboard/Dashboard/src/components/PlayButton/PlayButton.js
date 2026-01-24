import { TouchableOpacity, Text } from "react-native";
import styles from "./styles";

export default function PlayButton({ isPlaying, onPress }) {
  return (
    <TouchableOpacity
      style={styles.playButton}
      onPress={onPress}
    >
      <Text style={styles.playButtonText}>
        {isPlaying ? "⏸ PAUSE" : "▶ PLAY"}
      </Text>
    </TouchableOpacity>
  );
}
