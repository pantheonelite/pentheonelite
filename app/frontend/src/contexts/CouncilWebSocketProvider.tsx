/**
 * Council WebSocket Provider
 *
 * Manages a single WebSocket connection shared across all components.
 * Prevents multiple connections and connection spam.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import type {
  ConsensusEvent,
  CouncilEvent,
  ErrorEvent,
  TradeEvent,
} from "../hooks/useCouncilWebSocket";

// Re-export types for convenience
export type { ConsensusEvent, CouncilEvent, ErrorEvent, TradeEvent };

interface CouncilWebSocketContextType {
  isConnected: boolean;
  lastMessage: CouncilEvent | null;
  sendMessage: (data: any) => void;
  subscribe: (councilId?: number) => void;
  addTradeListener: (id: string, callback: (event: TradeEvent) => void) => void;
  removeTradeListener: (id: string) => void;
  addConsensusListener: (
    id: string,
    callback: (event: ConsensusEvent) => void
  ) => void;
  removeConsensusListener: (id: string) => void;
}

const CouncilWebSocketContext = createContext<
  CouncilWebSocketContextType | undefined
>(undefined);

// Get WebSocket URL
const getWebSocketUrl = () => {
  if (
    process.env.NEXT_PUBLIC_WS_URL &&
    process.env.NEXT_PUBLIC_WS_URL.length > 0
  ) {
    return process.env.NEXT_PUBLIC_WS_URL as string;
  }

  if (typeof window !== "undefined") {
    // Check if we're in production (handle both with and without www)
    const hostname = window.location.hostname;
    if (hostname === 'pantheonelite.ai' || hostname === 'www.pantheonelite.ai') {
      // Production: Use secure WebSocket
      return 'wss://api.pantheonelite.ai';
    }
    // Check if using HTTPS locally (for testing)
    if (window.location.protocol === 'https:') {
      return 'wss://api.pantheonelite.ai';
    }
    // Development: Use insecure WebSocket
    return 'ws://localhost:8000';
  }
  // SSR fallback
  return "ws://localhost:8000";
};

export function CouncilWebSocketProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<CouncilEvent | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  // Listener maps
  const tradeListenersRef = useRef<Map<string, (event: TradeEvent) => void>>(
    new Map()
  );
  const consensusListenersRef = useRef<
    Map<string, (event: ConsensusEvent) => void>
  >(new Map());

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    clearTimers();
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // 30 seconds
  }, [clearTimers]);

  const connect = useCallback(() => {
    // Don't create new connection if already connecting or connected
    if (
      wsRef.current?.readyState === WebSocket.CONNECTING ||
      wsRef.current?.readyState === WebSocket.OPEN
    ) {
      console.log("WebSocket already connecting or connected, skipping...");
      return;
    }

    try {
      const baseUrl = getWebSocketUrl();
      console.log(
        "Creating WebSocket connection to:",
        `${baseUrl}/api/v1/ws/council-trades`
      );
      const ws = new WebSocket(`${baseUrl}/api/v1/ws/council-trades`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("✅ WebSocket connected to council trades");
        setIsConnected(true);
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        try {
          const data: CouncilEvent = JSON.parse(event.data);
          setLastMessage(data);

          // Handle different message types
          switch (data.type) {
            case "consensus":
              // Notify all consensus listeners
              consensusListenersRef.current.forEach((callback) =>
                callback(data)
              );
              break;
            case "trade":
              // Notify all trade listeners
              tradeListenersRef.current.forEach((callback) => callback(data));
              break;
            case "pong":
              // Heartbeat received - connection is healthy
              break;
            case "subscription_confirmed":
              console.log(
                "Subscription confirmed for council:",
                data.council_id
              );
              break;
            case "error":
              console.error("WebSocket error message:", data.message);
              break;
            default:
              console.log("Unknown message type:", data);
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.warn("⚠️ WebSocket connection error (this is normal if backend WebSocket not configured)", error.type);
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log("WebSocket disconnected:", event.code, event.reason);
        setIsConnected(false);
        clearTimers();
        wsRef.current = null;

        // Auto-reconnect if enabled
        if (shouldReconnectRef.current) {
          console.log("Scheduling reconnect in 5 seconds...");
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log("Attempting to reconnect...");
            connect();
          }, 5000); // 5 seconds
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket connection:", error);
      setIsConnected(false);

      // Retry connection
      if (shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      }
    }
  }, [startHeartbeat, clearTimers]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not connected. Cannot send message.");
    }
  }, []);

  const subscribe = useCallback(
    (councilId?: number) => {
      if (councilId !== undefined) {
        sendMessage({
          type: "subscribe_council",
          council_id: councilId,
        });
      }
    },
    [sendMessage]
  );

  // Listener management
  const addTradeListener = useCallback(
    (id: string, callback: (event: TradeEvent) => void) => {
      tradeListenersRef.current.set(id, callback);
    },
    []
  );

  const removeTradeListener = useCallback((id: string) => {
    tradeListenersRef.current.delete(id);
  }, []);

  const addConsensusListener = useCallback(
    (id: string, callback: (event: ConsensusEvent) => void) => {
      consensusListenersRef.current.set(id, callback);
    },
    []
  );

  const removeConsensusListener = useCallback((id: string) => {
    consensusListenersRef.current.delete(id);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      console.log("Cleaning up WebSocket connection...");
      shouldReconnectRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []); // Empty dependency array - only run once on mount

  const value: CouncilWebSocketContextType = {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    addTradeListener,
    removeTradeListener,
    addConsensusListener,
    removeConsensusListener,
  };

  return (
    <CouncilWebSocketContext.Provider value={value}>
      {children}
    </CouncilWebSocketContext.Provider>
  );
}

export function useCouncilWebSocketContext() {
  const context = useContext(CouncilWebSocketContext);
  if (context === undefined) {
    throw new Error(
      "useCouncilWebSocketContext must be used within a CouncilWebSocketProvider"
    );
  }
  return context;
}
