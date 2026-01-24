import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  /* =======================
     BASE CONTAINER
  ======================= */
  container: {
    flex: 1,
    backgroundColor: colors.darkBg,
    padding: 30,
  },

  /* =======================
     MAIN DASHBOARD ROW
  ======================= */
  mainRow: {
    flexDirection: 'row',
    gap: 30,
    alignItems: 'stretch',
    marginTop: 10,
  },

  leftColumn: {
    flex: 0.8,
  },

  leftPanel: {
    backgroundColor: colors.panelBg,
    borderRadius: 18,
    padding: 25,
    borderWidth: 2,
    borderColor: colors.cyanBorder,
    height: '100%',
    flexDirection: 'column',
    justifyContent: 'space-between',
  },

  uploadContent: {
    flex: 1,
  },

  rightColumn: {
    flex: 1,
    alignSelf: 'stretch',
  },

  rightPanel: {
    backgroundColor: colors.panelBg,
    borderRadius: 18,
    padding: 25,
    borderWidth: 2,
    borderColor: colors.cyanBorder,
    height: '100%',
  },
});
