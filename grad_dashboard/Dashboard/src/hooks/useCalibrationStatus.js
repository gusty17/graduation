import { useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:5000";

/**
 * useCalibrationStatus
 *
 * Polls the backend empty-room calibration status once per second while
 * `active` is true. On startup the backend spends a few minutes measuring the
 * empty room before it begins predicting; this hook surfaces that phase and
 * countdown so the UI can show a "calibrating" banner.
 *
 * Returns: { phase: "calibrating" | "predicting", remaining, duration } | null
 * Polling stops automatically once the backend reports "predicting".
 */
export default function useCalibrationStatus(active) {
  const [status, setStatus] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!active) {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
      setStatus(null);
      return;
    }

    let stopped = false;

    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/calibration/status`);
        const data = await res.json();
        if (stopped) return;
        setStatus(data);
        if (data.phase === "predicting" && timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      } catch (err) {
        // Backend not up yet or transient error - keep polling.
      }
    };

    poll();
    timerRef.current = setInterval(poll, 1000);

    return () => {
      stopped = true;
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [active]);

  return status;
}
