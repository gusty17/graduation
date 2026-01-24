import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  statusCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.darkPanelBg,
    padding: 20,
    borderRadius: 14,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: colors.cyanTransparent25,
  },
  
  statusIcon: {
    fontSize: 26,
    marginRight: 15,
  },
  
  statusTitle: {
    color: colors.textCyan,
    fontSize: 11,
    letterSpacing: 2,
  },
  
  statusValue: {
    color: colors.textLime,
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 3,
  },
});
