import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
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
});
