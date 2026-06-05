import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  headerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.headerBg,
    padding: 25,
    borderRadius: 18,
    borderBottomWidth: 3,
    borderBottomColor: colors.cyan,
    marginBottom: 25,
  },
  
  headerIcon: {
    fontSize: 36,
    marginRight: 15,
  },
  
  headerTitle: {
    color: colors.textCyan,
    fontSize: 22,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  
  headerSubtitle: {
    color: colors.textLime,
    marginTop: 4,
    fontSize: 13,
  },
});
