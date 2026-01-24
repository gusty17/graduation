import { StyleSheet } from 'react-native';
import colors from '../../styles/colors';

export default StyleSheet.create({
  timestampCard: {
    borderRadius: 14,
    paddingBottom: 15,
    marginBottom: 20,
  },
  
  timestampHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  
  timestampLabel: {
    color: colors.textLime,
    letterSpacing: 2,
  },
  
  timestampBadge: {
    backgroundColor: colors.timestampBg,
    paddingHorizontal: 15,
    paddingVertical: 6,
    borderRadius: 10,
  },
  
  timestampBadgeText: {
    color: colors.textCyan,
    fontWeight: 'bold',
  },

  /* custom slider */
  sliderTrack: {
    height: 6,
    backgroundColor: colors.cyanTransparent25,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: -22,
  },
  
  sliderFill: {
    height: '100%',
    backgroundColor: colors.cyan,
  },
  
  slider: {
    height: 40,
  },

  timestampMarks: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  
  timestampMark: {
    color: colors.textLime,
    fontSize: 11,
  },
});
