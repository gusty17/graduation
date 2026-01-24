import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  playButton: {
    alignSelf: 'center',
    marginVertical: 15,
    marginBottom: 25,
    backgroundColor: colors.cyan,
    paddingHorizontal: 30,
    paddingVertical: 10,
    borderRadius: 8,
  },

  playButtonText: {
    color: colors.textDark,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
});
