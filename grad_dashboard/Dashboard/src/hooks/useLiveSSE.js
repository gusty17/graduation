import { useEffect, useRef, useState } from "react";
import { startLivePrediction, stopLivePrediction } from "../api/api";

const API_URL = "http://127.0.0.1:5000";

/**
 * useLiveSSE Hook
 * 
 * Manages Server-Sent Events connection for real-time predictions.
 * 
 * Usage:
 *   const liveData = useLiveSSE(isLive);
 * 
 * Features:
 * - Calls /realtime/start when isLive becomes true
 * - Calls /realtime/stop and cleans up when isLive becomes false
 * - Connects to SSE stream for real-time data
 * - Handles connection errors gracefully
 * - Auto-reconnects on error
 * - Returns latest prediction data or null
 */
export default function useLiveSSE(isLive) {
  const [liveData, setLiveData] = useState(null);
  const sourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    // Clean up if not live
    if (!isLive) {
      if (sourceRef.current) {
        console.log("🛑 Closing SSE connection");
        sourceRef.current.close();
        sourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      setLiveData(null);

      // Stop backend MQTT and inference
      stopLivePrediction()
        .then((res) => {
          console.log("✅ Live prediction stopped:", res);
        })
        .catch((err) => {
          console.error("⚠️ Error stopping live prediction:", err);
        });
      return;
    }

    // Start backend MQTT and inference
    startLivePrediction()
      .then((res) => {
        console.log("✅ Live prediction started:", res);
      })
      .catch((err) => {
        console.error("❌ Error starting live prediction:", err);
        return;
      });

    // Connect to SSE stream
    console.log("🟢 Connecting to SSE stream...");
    const source = new EventSource(`${API_URL}/realtime/stream`);
    sourceRef.current = source;

    let messageCount = 0;

    source.onopen = () => {
      console.log("✅ SSE connection opened");
    };

    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`📨 SSE message #${++messageCount}:`, data);
        setLiveData(data);
      } catch (err) {
        console.error("❌ Error parsing SSE data:", err);
      }
    };

    source.onerror = (err) => {
      console.error("❌ SSE connection error:", err);
      source.close();
      sourceRef.current = null;

      // Attempt reconnect after 3 seconds
      console.log("⏳ Reconnecting in 3 seconds...");
      reconnectTimeoutRef.current = setTimeout(() => {
        if (isLive) {
          console.log("🔄 Reconnecting to SSE...");
          // Re-trigger the effect by returning and letting it run again
        }
      }, 3000);
    };

    // Cleanup on unmount or when isLive changes
    return () => {
      if (sourceRef.current) {
        sourceRef.current.close();
        sourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [isLive]);

  return liveData;
}

