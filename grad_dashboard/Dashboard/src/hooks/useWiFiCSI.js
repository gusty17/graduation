import { useState, useEffect } from "react";
import { predictCSV } from "../api/api";

export default function useWiFiCSI() {
  const [isPlaying, setIsPlaying] = useState(false);

  const [currentFile, setCurrentFile] = useState(null);
  const [detectionStatus, setDetectionStatus] = useState("Awaiting Data");
  const [currentReading, setCurrentReading] = useState("- persons");

  const [timestamps, setTimestamps] = useState([]);
  const [predictions, setPredictions] = useState([]);

  const [selectedTimestamp, setSelectedTimestamp] = useState(0);
  const [activePerson, setActivePerson] = useState(0);

  // 🔁 This now represents CONFIDENCE, not accuracy
  const [confidence, setConfidence] = useState(0);

  /* ================= FILE SELECT (WEB) ================= */
  const handleFileSelect = (file) => {
    console.log("📁 Web file selected:", file);

    setCurrentFile(file);
    setDetectionStatus("File Loaded");
    setCurrentReading("- persons");

    setPredictions([]);
    setTimestamps([]);
    setSelectedTimestamp(0);
    setActivePerson(0);
    setConfidence(0);
    setIsPlaying(false);
  };

  /* ================= ANALYZE ================= */
  const processFile = async () => {
    if (!currentFile) {
      console.warn("❌ No file selected");
      return;
    }

    try {
      setDetectionStatus("Processing...");

      const results = await predictCSV(currentFile);
      console.log("✅ Backend results:", results);

      setPredictions(results);
      setTimestamps(results.map((r) => r.timestamp));

      // Apply first prediction by default
      applyPrediction(0, results);

      setDetectionStatus("Detection Complete");
    } catch (err) {
      console.error("❌ Prediction error:", err);
      setDetectionStatus("Error");
    }
  };

  /* ================= APPLY PREDICTION ================= */
  const applyPrediction = (index, data = predictions) => {
    const pred = data[index];
    if (!pred) return;

    setSelectedTimestamp(index);
    setActivePerson(pred.person_count);
    setCurrentReading(`${pred.person_count} persons`);

    // ✅ REAL MODEL CONFIDENCE (from backend)
    setConfidence(pred.confidence ?? 0);
  };

  /* ================= SLIDER ================= */
  const handleTimestampChange = (index) => {
    setIsPlaying(false);
    applyPrediction(index);
  };

  /* ================= PLAY / PAUSE ================= */
  const togglePlay = () => {
    if (!predictions.length) return;
    setIsPlaying((prev) => !prev);
  };

  /* ================= AUTO PLAY EFFECT ================= */
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setSelectedTimestamp((prev) => {
        const next = prev + 1;

        if (next >= predictions.length) {
          setIsPlaying(false); // stop at end
          return prev;
        }

        applyPrediction(next);
        return next;
      });
    }, 800); // ⏱ playback speed

    return () => clearInterval(interval);
  }, [isPlaying, predictions]);

  /* ================= CLEAR ================= */
  const clearFile = () => {
    setCurrentFile(null);
    setPredictions([]);
    setTimestamps([]);
    setSelectedTimestamp(0);
    setActivePerson(0);
    setConfidence(0);
    setDetectionStatus("Awaiting Data");
    setCurrentReading("- persons");
    setIsPlaying(false);
  };

  return {
    currentFile,
    detectionStatus,
    currentReading,
    timestamps,
    selectedTimestamp,
    activePerson,
    confidence,
    isPlaying,
    predictions,
    handleFileSelect,
    processFile,
    clearFile,
    togglePlay,
    setSelectedTimestamp: handleTimestampChange,
  };
}
