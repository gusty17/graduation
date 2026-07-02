import { StyleSheet } from "react-native";
import colors from "../../styles/colors";

export default StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },

  card: {
    width: "100%",
    maxWidth: 520,
    backgroundColor: colors.panelBg,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cyanTransparent25,
    padding: 24,
  },

  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },

  title: {
    color: colors.textCyan,
    fontWeight: "bold",
    fontSize: 15,
    letterSpacing: 2,
  },

  close: {
    color: colors.textCyan,
    fontSize: 18,
    fontWeight: "bold",
    paddingHorizontal: 6,
  },

  hint: {
    color: colors.textSubtle,
    fontSize: 12,
    marginBottom: 12,
    lineHeight: 18,
  },

  error: {
    color: "#d9534f",
    fontSize: 12,
    marginBottom: 10,
  },

  warn: {
    color: "#f0ad4e",
    fontSize: 12,
    marginTop: 8,
    marginBottom: 4,
  },

  fieldLabel: {
    color: colors.textCyan,
    fontSize: 11,
    letterSpacing: 2,
    marginTop: 14,
    marginBottom: 8,
  },

  labelRow: {
    flexDirection: "row",
    gap: 10,
    flexWrap: "wrap",
  },

  chip: {
    borderWidth: 1.5,
    borderColor: colors.cyanTransparent30,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },

  chipActive: {
    backgroundColor: colors.cyan,
    borderColor: colors.cyan,
  },

  chipText: {
    color: colors.textCyan,
    fontWeight: "bold",
    letterSpacing: 1,
  },

  chipTextActive: {
    color: colors.textDark,
  },

  input: {
    backgroundColor: colors.darkBg,
    borderWidth: 1,
    borderColor: colors.cyanTransparent25,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    color: colors.textLime,
    fontSize: 15,
  },

  existing: {
    color: colors.textSubtle,
    fontSize: 11,
    marginTop: 14,
    lineHeight: 16,
  },

  primaryBtn: {
    backgroundColor: colors.lime,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 22,
  },

  primaryBtnText: {
    color: colors.textDark,
    fontWeight: "bold",
    letterSpacing: 2,
  },

  ghostBtn: {
    borderWidth: 2,
    borderColor: colors.cyan,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 22,
  },

  ghostBtnText: {
    color: colors.textCyan,
    fontWeight: "bold",
    letterSpacing: 2,
  },

  /* recording */
  recTitle: {
    color: colors.textCyan,
    fontWeight: "bold",
    fontSize: 15,
    textAlign: "center",
    marginBottom: 6,
  },

  countdown: {
    color: colors.textLime,
    fontSize: 54,
    fontWeight: "bold",
    textAlign: "center",
  },

  rxRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 18,
    justifyContent: "space-between",
  },

  rxBox: {
    flex: 1,
    backgroundColor: colors.darkBg,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.cyanTransparent20,
    paddingVertical: 14,
    alignItems: "center",
  },

  rxName: {
    color: colors.textCyan,
    fontSize: 12,
    letterSpacing: 2,
    fontWeight: "bold",
  },

  rxCount: {
    fontSize: 26,
    fontWeight: "bold",
    marginVertical: 4,
  },

  rxState: {
    color: colors.textSubtle,
    fontSize: 10,
  },

  stopBtn: {
    backgroundColor: "#d9534f",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 22,
  },

  stopBtnText: {
    color: "#fff",
    fontWeight: "bold",
    letterSpacing: 2,
  },

  summaryLine: {
    color: colors.textLime,
    fontSize: 15,
    textAlign: "center",
    marginBottom: 6,
  },

  summaryBtnRow: {
    flexDirection: "row",
    gap: 12,
  },
});
