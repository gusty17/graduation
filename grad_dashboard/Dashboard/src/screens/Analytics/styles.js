import { StyleSheet } from "react-native";
import colors from "../../styles/colors";

export default StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.darkBg,
    padding: 30,
  },

  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.darkBg,
  },

  title: {
    color: colors.textCyan,
    fontSize: 22,
    fontWeight: "bold",
    letterSpacing: 3,
    textAlign: "center",
  },

  fileLabel: {
    color: colors.textCyan,
    textAlign: "center",
    marginTop: 5,
  },

  dayLabel: {
    color: colors.textLime,
    textAlign: "center",
    marginBottom: 25,
  },

  statsTableBox: {
    backgroundColor: colors.panelBg,
    borderRadius: 18,
    padding: 25,
    paddingHorizontal: 70,
    borderWidth: 1,
    borderColor: colors.cyanBorder,
    marginBottom: 30,
    position: "relative",
  },

  topRow: {
    flexDirection: "row",
    gap: 30,
  },

  statsCol: {
    flex: 0.4,
  },

  tableCol: {
    flex: 0.6,
  },
   /* =======================
     BACK BUTTON
  ======================= */
  backButton: {
    position: "absolute",
    top: 30,
    right: 10,
    zIndex: 100,
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: colors.cyanBorder,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.textCyan,
    marginBottom: 50,
  },

  backButtonText: {
    color: colors.textDark,
    fontSize: 14,
    fontWeight: "bold",
    letterSpacing: 1,
  },

  leftArrow: {
    position: "absolute",
    left: 10,
    top: "50%",
    transform: [{ translateY: -20 }],
    zIndex: 5,
  },

  rightArrow: {
    position: "absolute",
    right: 10,
    top: "50%",
    transform: [{ translateY: -20 }],
    zIndex: 5,
  },

  arrowText: {
    fontSize: 40,
    color: colors.textCyan,
  },

  arrowDisabled: {
    opacity: 0.25,
  },

  chartSection: {
    backgroundColor: colors.panelBg,
    borderRadius: 18,
    padding: 25,
    borderWidth: 1,
    borderColor: colors.cyanBorder,
    marginBottom: 40,
  },

  sectionTitle: {
    color: colors.textCyan,
    fontWeight: "bold",
    letterSpacing: 2,
    marginBottom: 15,
    textAlign: "center",
  },
  /* ================= VIEW TOGGLE ================= */
viewToggle: {
  flexDirection: "row",
  justifyContent: "center",
  gap: 20,
  marginBottom: 25,
},

toggleBtn: {
  paddingVertical: 10,
  paddingHorizontal: 24,
  borderRadius: 12,
  borderWidth: 1,
  borderColor: colors.cyanBorder,
},

toggleBtnActive: {
  backgroundColor: colors.cyan,
},

toggleText: {
  color: colors.textDark,
  fontWeight: "bold",
  letterSpacing: 1.5,
},

/* ================= FILE NAV BUTTONS ================= */
fileNav: {
  flexDirection: "row",
  justifyContent: "space-between",
  marginBottom: 20,
},

navBtn: {
  paddingVertical: 8,
  paddingHorizontal: 18,
  borderRadius: 10,
  borderWidth: 1,
  borderColor: colors.cyanBorder,
},

navText: {
  color: colors.textCyan,
  fontWeight: "bold",
  letterSpacing: 1.5,
},

/* ================= ALL FILES TABLE ================= */
allTableRow: {
  flexDirection: "row",
  justifyContent: "space-between",
  paddingVertical: 10,
  borderBottomWidth: 1,
  borderColor: "rgba(0,255,255,0.15)",
},

fileCell: {
  flex: 0.4,
  color: colors.textLime,
  fontSize: 14,
},

timeCell: {
  flex: 0.35,
  color: colors.textCyan,
  fontSize: 14,
},

personCell: {
  flex: 0.25,
  color: colors.textCyan,
  fontSize: 16,
  fontWeight: "bold",
  textAlign: "right",
},

});














 