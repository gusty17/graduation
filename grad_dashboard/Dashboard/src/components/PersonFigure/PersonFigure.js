import { View, Text } from 'react-native';
import Svg, { Circle, Ellipse, Path, Line } from 'react-native-svg';
import styles from './styles';

export default function PersonFigure({ label, active }) {
  // MATCH CORRECT UI COLORS
  const activeColor = '#00ffff';            // Bright cyan
  const inactiveColor = '#1b3a4b';          // Dark blue silhouette
  const color = active ? activeColor : inactiveColor;

  return (
    <View
      style={[
        styles.personContainer,
        active && styles.personActive,
      ]}
    >
      <Svg width="100" height="150" viewBox="0 0 100 150">
        {/* Head */}
        <Circle cx="50" cy="20" r="14" fill={color} />

        {/* Neck */}
        <Line
          x1="50"
          y1="35"
          x2="50"
          y2="42"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
        />

        {/* Body */}
        <Ellipse cx="50" cy="75" rx="18" ry="30" fill={color} />

        {/* Arms */}
        <Path
          d="M32 55 Q18 75 22 95"
          stroke={color}
          strokeWidth="6"
          fill="none"
          strokeLinecap="round"
        />
        <Path
          d="M68 55 Q82 75 78 95"
          stroke={color}
          strokeWidth="6"
          fill="none"
          strokeLinecap="round"
        />

        {/* Legs */}
        <Path
          d="M44 105 L40 130 L38 145"
          stroke={color}
          strokeWidth="7"
          fill="none"
          strokeLinecap="round"
        />
        <Path
          d="M56 105 L60 130 L62 145"
          stroke={color}
          strokeWidth="7"
          fill="none"
          strokeLinecap="round"
        />

        {/* Feet */}
        <Ellipse cx="37" cy="147" rx="6" ry="3" fill={color} />
        <Ellipse cx="63" cy="147" rx="6" ry="3" fill={color} />
      </Svg>

      <Text
        style={[
          styles.personLabel,
          active && styles.personLabelActive,
        ]}
      >
        {label}
      </Text>
    </View>
  );
}
