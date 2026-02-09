import { StyleSheet } from "react-native";
import colors from "../../styles/colors";

export default StyleSheet.create({
  actionCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 15,
    marginTop: 20,
    flexWrap: "wrap",   // ✅ ADD THIS
  },

  analyzeButton: {
    backgroundColor: colors.cyan,
    paddingVertical: 14,
    paddingHorizontal: 26,
    borderRadius: 12,
  },

  analyzeButtonText: {
    color: colors.textDark,
    fontWeight: "bold",
    letterSpacing: 2,
  },

  clearButton: {
    borderWidth: 2,
    borderColor: colors.cyan,
    paddingVertical: 14,
    paddingHorizontal: 26,
    borderRadius: 12,
  },

  clearButtonText: {
    color: colors.cyan,
    fontWeight: "bold",
    letterSpacing: 2,
  },

  /* =======================
     ANALYTICS BUTTON
  ======================= */
  analyticsButton: {
    backgroundColor: "rgba(0,255,255,0.12)",
    borderWidth: 1.5,
    borderColor: colors.cyan,
    paddingVertical: 14,
    paddingHorizontal: 26,
    borderRadius: 12,
  },

  analyticsButtonText: {
    color: colors.textCyan,
    fontWeight: "bold",
    letterSpacing: 2,
  },
});
