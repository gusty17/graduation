import React, { createContext, useContext } from "react";
import useWiFiCSI from "../hooks/useWiFiCSI";

const WiFiCSIContext = createContext(null);

export function WiFiCSIProvider({ children }) {
  const wifi = useWiFiCSI();

  return (
    <WiFiCSIContext.Provider value={wifi}>
      {children}
    </WiFiCSIContext.Provider>
  );
}

export function useWiFiCSIContext() {
  const context = useContext(WiFiCSIContext);
  if (!context) {
    throw new Error(
      "useWiFiCSIContext must be used inside WiFiCSIProvider"
    );
  }
  return context;
}
