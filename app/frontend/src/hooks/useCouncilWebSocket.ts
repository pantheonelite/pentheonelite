/**
 * WebSocket hook for real-time council trading updates.
 *
 * Connects to /ws/council-trades endpoint and handles:
 * - Consensus decisions from agent debates
 * - Trade executions
 * - Auto-reconnection on disconnect
 * - Ping/pong heartbeat
 */

import { useEffect, useRef, useState, useCallback } from 'react';

// In development, use relative URL to go through Vite proxy
// In production, use NEXT_PUBLIC_WS_URL env var
const getWebSocketUrl = () => {
  if (process.env.NEXT_PUBLIC_WS_URL && process.env.NEXT_PUBLIC_WS_URL.length > 0) {
    return process.env.NEXT_PUBLIC_WS_URL as string;
  }

  // Use backend URL (browser only)
  if (typeof window !== 'undefined') {
    // Check if we're in production
    if (window.location.hostname === 'pantheonelite.ai') {
      return 'wss://api.pantheonelite.ai';
    }
    // Development: Always use backend port 8000, not frontend port
    return 'ws://localhost:8000';
  }
  // SSR fallback
  return 'ws://localhost:8000';
};

export interface ConsensusEvent {
  type: 'consensus';
  council_id: number;
  council_name: string;
  decision: string;
  symbol: string;
  confidence: number;
  timestamp: string;
}

export interface TradeEvent {
  type: 'trade';
  council_id: number;
  council_name: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  timestamp: string;
}

export interface PongEvent {
  type: 'pong';
  timestamp: string;
}

export interface SubscriptionConfirmedEvent {
  type: 'subscription_confirmed';
  council_id: number;
  timestamp: string;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

export type CouncilEvent =
  | ConsensusEvent
  | TradeEvent
  | PongEvent
  | SubscriptionConfirmedEvent
  | ErrorEvent;

export interface UseCouncilWebSocketOptions {
  autoConnect?: boolean;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  onConsensus?: (event: ConsensusEvent) => void;
  onTrade?: (event: TradeEvent) => void;
  onError?: (error: ErrorEvent) => void;
}

export interface UseCouncilWebSocketReturn {
  isConnected: boolean;
  lastMessage: CouncilEvent | null;
  sendMessage: (data: any) => void;
  subscribe: (councilId?: number) => void;
  connect: () => void;
  disconnect: () => void;
}

export function useCouncilWebSocket(
  options: UseCouncilWebSocketOptions = {}
): UseCouncilWebSocketReturn {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
    heartbeatInterval = 30000,
    onConsensus,
    onTrade,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<CouncilEvent | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

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
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval, clearTimers]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const baseUrl = getWebSocketUrl();
      const ws = new WebSocket(`${baseUrl}/api/v1/ws/council-trades`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to council trades');
        setIsConnected(true);
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        try {
          const data: CouncilEvent = JSON.parse(event.data);
          setLastMessage(data);

          // Call specific handlers
          switch (data.type) {
            case 'consensus':
              onConsensus?.(data);
              break;
            case 'trade':
              onTrade?.(data);
              break;
            case 'error':
              onError?.(data);
              break;
            case 'pong':
              // Heartbeat received
              break;
            case 'subscription_confirmed':
              console.log('Subscription confirmed for council:', data.council_id);
              break;
            default:
              console.log('Unknown message type:', data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        clearTimers();

        // Auto-reconnect if enabled
        if (shouldReconnectRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setIsConnected(false);

      // Retry connection
      if (shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    }
  }, [reconnectInterval, startHeartbeat, onConsensus, onTrade, onError, clearTimers]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearTimers();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, [clearTimers]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  const subscribe = useCallback((councilId?: number) => {
    if (councilId !== undefined) {
      sendMessage({
        type: 'subscribe_council',
        council_id: councilId,
      });
    }
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      shouldReconnectRef.current = true;
      connect();
    }

    return () => {
      shouldReconnectRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Only depend on autoConnect, not connect/disconnect

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    connect,
    disconnect,
  };
}
