import { StyleSheet } from "react-native";
import colors from "../../styles/colors";

export default StyleSheet.create({
  /* ================= CARD BASE ================= */
  card: {
    backgroundColor: colors.panelBg,
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: colors.cyanBorder,
    marginBottom: 30,
  },

  cardTitle: {
    color: colors.textCyan,
    fontWeight: "bold",
    letterSpacing: 2,
    marginBottom: 15,
    textAlign: "center",
  },

  /* ================= STATS ROW ================= */
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginVertical: 8,
  },

  label: {
    color: colors.textLime,
    fontSize: 15,
    letterSpacing: 1,
  },

  value: {
    color: colors.textCyan,
    fontSize: 18,
    fontWeight: "bold",
  },

  /* ================= TABLE ================= */
  tableHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    borderBottomWidth: 1,
    borderColor: colors.cyanBorder,
    paddingBottom: 10,
    marginBottom: 10,
  },

  tableHeaderText: {
    color: colors.textCyan,
    fontSize: 15,
    fontWeight: "bold",
  },

  tableRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
  },

  /* LEFT COLUMN (TIME) */
  tableCellLeft: {
    flex: 1,
    color: colors.textLime,
    fontSize: 15,
  },

  /* RIGHT COLUMN (PERSON COUNT) */
  tableCellRight: {
    color: colors.textCyan,
    fontSize: 18,
    fontWeight: "bold",
    textAlign: "right",
    marginLeft: 40,   // ✅ extra spacing between columns
    marginRight: 30,
  },

  /* ================= HEATMAP ================= */
  heatmapGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    justifyContent: "center",
  },

  heatmapCell: {
    width: 40,
    height: 40,
    borderRadius: 6,
    justifyContent: "center",
    alignItems: "center",
  },

  heatmapText: {
    color: colors.darkBg,
    fontWeight: "bold",
    fontSize: 14,
  },

  /* ================= OPTIONAL INNER BOX ================= */
  innerBox: {
    backgroundColor: "rgba(0,255,255,0.06)",
    borderRadius: 14,
    padding: 15,
    borderWidth: 1,
    borderColor: colors.cyanBorder,
  },
});
