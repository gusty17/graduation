import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  resultCard: {
    borderRadius: 14,
    padding: 20,
    marginTop: 20,
    backgroundColor: colors.cyanTransparent08,
    borderWidth: 1,
    borderColor: colors.cyanTransparent25,
  },
  
  sectionTitle: {
    color: colors.textCyan,
    textAlign: 'center',
    letterSpacing: 3,
    marginBottom: 25,
    fontWeight: 'bold',
  },

  /* PERSON FIGURES */
  personRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'flex-end',
    gap: 30,
    marginVertical: 30,
    minHeight: 170,
  },

  personContainer: {
    alignItems: 'center',
    opacity: 0.25,
    transform: [{ scale: 0.95 }],
  },

  personActive: {
    opacity: 1,
    transform: [{ scale: 1.1 }],
    elevation: 10,
  },

  personLabel: {
    marginTop: 6,
    color: colors.textSubtle,
    fontSize: 11,
    letterSpacing: 1.5,
  },

  personLabelActive: {
    color: colors.textCyan,
    fontWeight: 'bold',
  },

  /* RESULT ROW */
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 6,
  },
  
  resultLabel: {
    color: colors.textLime,
    letterSpacing: 1.5,
  },
  
  resultValue: {
    color: colors.textCyan,
    fontWeight: 'bold',
  },

  /* CONFIDENCE BAR */
  confidenceBar: {
    height: 10,
    backgroundColor: colors.cyanTransparent20,
    borderRadius: 6,
    marginTop: 15,
    overflow: 'hidden',
  },
  
  confidenceFill: {
    height: '100%',
    backgroundColor: colors.cyan,
  },

  /* INNER BOX */
  resultInnerBox: {
    marginTop: 20,
    padding: 18,
    borderRadius: 14,
    backgroundColor: colors.cyanTransparent08,
    borderWidth: 1,
    borderColor: colors.cyanTransparent25,
  },
});
