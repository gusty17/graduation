import { View, Text } from 'react-native';
import PersonFigure from '../PersonFigure/PersonFigure';
import styles from './styles';

export default function DetectionResults({ confidence, activePerson }) {
  return (
    <View style={styles.resultCard}>
      <Text style={styles.sectionTitle}>DETECTION RESULT</Text>

      <View style={styles.personRow}>
        {[1, 2, 3].map((n) => (
          <PersonFigure
            key={n}
            label={`${n} Person${n > 1 ? 's' : ''}`}
            active={activePerson >= n}   
          />
        ))}
      </View>

      {/* INNER BOX */}
      <View style={styles.resultInnerBox}>
        <View style={styles.resultRow}>
          <Text style={styles.resultLabel}>OCCUPANCY</Text>
          <Text style={styles.resultValue}>
            {activePerson} {activePerson === 1 ? 'Person' : 'Persons'}
          </Text>
        </View>

        <View style={styles.resultRow}>
          <Text style={styles.resultLabel}>PREDICTION CONFIDENCE</Text>
          <Text style={styles.resultValue}>{confidence}%</Text>
        </View>

        <View style={styles.confidenceBar}>
          <View
            style={[
              styles.confidenceFill,
              { width: `${confidence}%` },
            ]}
          />
        </View>
      </View>
    </View>
  );
}
