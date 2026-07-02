import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchCollectSessions,
  fetchCollectStatus,
  startCollection,
  stopCollection,
} from "../api/api";

/**
 * useCollection(active)
 *
 * Drives the training-data collector. While `active` (the modal is open) it
 * polls /collect/status once per second for the live countdown + per-receiver
 * row counts, and loads the existing sessions so the form can prefill the next
 * session name and warn on overwrite.
 *
 * Returns { status, sessions, error, start, stop, refreshSessions }.
 */
export default function useCollection(active) {
  const [status, setStatus] = useState(null);
  const [sessions, setSessions] = useState({
    sessions: [],
    suggested: "session_01",
    labels: ["0p", "1p", "2p"],
    default_duration: 600,
  });
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await fetchCollectSessions());
    } catch (e) {
      /* backend not up yet — keep defaults */
    }
  }, []);

  const poll = useCallback(async () => {
    try {
      setStatus(await fetchCollectStatus());
    } catch (e) {
      /* transient — keep last status */
    }
  }, []);

  useEffect(() => {
    if (!active) {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
      return;
    }
    refreshSessions();
    poll();
    timerRef.current = setInterval(poll, 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [active, poll, refreshSessions]);

  const start = useCallback(async (opts) => {
    setError(null);
    try {
      setStatus(await startCollection(opts));
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }, []);

  const stop = useCallback(async () => {
    setError(null);
    try {
      await stopCollection();
      await poll();
      await refreshSessions();
    } catch (e) {
      setError(e.message);
    }
  }, [poll, refreshSessions]);

  return { status, sessions, error, start, stop, refreshSessions };
}
