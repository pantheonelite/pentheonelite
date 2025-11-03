import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import AppKitProvider from "./contexts/AppKitProvider";
import { NodeProvider } from "./contexts/node-context";
import { ThemeProvider } from "./providers/theme-provider";
import { CouncilWebSocketProvider } from "./contexts/CouncilWebSocketProvider";

import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AppKitProvider cookies={null}>
        <CouncilWebSocketProvider>
          <NodeProvider>
            <App />
          </NodeProvider>
        </CouncilWebSocketProvider>
      </AppKitProvider>
    </ThemeProvider>
  </React.StrictMode>
);
