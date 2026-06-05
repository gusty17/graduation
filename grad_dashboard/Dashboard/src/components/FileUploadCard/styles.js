import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  uploadCard: {
    backgroundColor: 'transparent',
    flex: 1,
    borderRadius: 14,
    paddingTop: 0,
    marginTop: 0,
    marginBottom: 20,
  },
  
  uploadHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  
  uploadHeaderIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  
  uploadHeaderText: {
    color: colors.textCyan,
    letterSpacing: 3,
    fontWeight: 'bold',
  },
  
  uploadDivider: {
    height: 1,
    backgroundColor: colors.cyanTransparent30,
    marginVertical: 15,
  },
  
  systemReady: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.limeTransparent15,
    padding: 12,
    borderRadius: 10,
    marginBottom: 20,
  },
  
  greenDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.textLime,
    marginRight: 10,
  },
  
  systemReadyText: {
    color: colors.textLime,
    letterSpacing: 1.5,
    fontWeight: 'bold',
  },

  uploadZone: {
    borderWidth: 2,
    flex: 1, 
    borderStyle: 'dashed',
    borderColor: colors.cyan,
    borderRadius: 14,
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  uploadIcon: {
    fontSize: 42,
    marginBottom: 10,
  },
  
  uploadTitle: {
    color: colors.textCyan,
    fontWeight: 'bold',
    marginBottom: 5,
    textAlign: 'center',
  },
  
  uploadSubtitle: {
    color: colors.textLime,
    marginBottom: 20,
    textAlign: 'center',
  },
  
  selectBtn: {
    backgroundColor: colors.cyan,
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 10,
  },
  
  selectBtnText: {
    color: colors.textDark,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  
  fileName: {
    marginTop: 15,
    color: colors.textLime,
  },
});
