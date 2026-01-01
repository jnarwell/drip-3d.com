import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth0 } from '@auth0/auth0-react';

interface AnalysisMessage {
  type: 'connected' | 'instance_created' | 'instance_updated' | 'instance_deleted' | 'instance_evaluated' | 'pong';
  data?: any;
  message?: string;
}

interface WebSocketWithPing extends WebSocket {
  _pingInterval?: ReturnType<typeof setInterval>;
}

export function useAnalysisWebSocket() {
  const wsRef = useRef<WebSocketWithPing | null>(null);
  const queryClient = useQueryClient();
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectAttempts = useRef<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const connect = useCallback(async () => {
    if (!isAuthenticated) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Get token for WebSocket authentication
    let token = 'mock-dev-token';
    if (!import.meta.env.DEV) {
      try {
        token = await getAccessTokenSilently({
          authorizationParams: {
            audience: import.meta.env.VITE_AUTH0_AUDIENCE,
          },
        });
      } catch (error) {
        console.error('[WebSocket] Failed to get token:', error);
        return;
      }
    }

    // Build WebSocket URL from API URL or fallback to current host
    // Note: Backend endpoint is /ws/analyses (plural)
    let wsUrl: string;
    if (import.meta.env.DEV) {
      wsUrl = `ws://localhost:8000/ws/analyses?token=${encodeURIComponent(token)}`;
    } else {
      // Use the configured API URL for production
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const wsBaseUrl = apiUrl.replace(/^http/, 'ws').replace(/^https/, 'wss');
      wsUrl = `${wsBaseUrl}/ws/analyses?token=${encodeURIComponent(token)}`;
    }

    console.log('[WebSocket] Connecting to:', wsUrl.replace(token, '***'));
    const ws: WebSocketWithPing = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[WebSocket] Connected to Analysis updates');
      reconnectAttempts.current = 0;
      setIsConnected(true);

      // Send ping every 30 seconds to keep alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);

      ws._pingInterval = pingInterval;
      wsRef.current = ws;
    };

    ws.onmessage = (event) => {
      try {
        const message: AnalysisMessage = JSON.parse(event.data);
        console.log('[WebSocket] Received:', message.type);

        switch (message.type) {
          case 'connected':
            console.log('[WebSocket]', message.message);
            break;

          case 'instance_created':
          case 'instance_updated':
          case 'instance_evaluated':
            // Invalidate queries to refetch list
            queryClient.invalidateQueries({ queryKey: ['analyses'] });
            queryClient.invalidateQueries({ queryKey: ['model-instances'] });

            // Optimistically update the cache if we have the data
            if (message.data) {
              queryClient.setQueryData(['analyses'], (old: any[] | undefined) => {
                if (!old) return [message.data];

                const index = old.findIndex(item => item.id === message.data.id);
                if (index >= 0) {
                  // Update existing
                  const updated = [...old];
                  updated[index] = message.data;
                  return updated;
                } else {
                  // Add new
                  return [...old, message.data].sort((a, b) => a.name.localeCompare(b.name));
                }
              });
            }
            break;

          case 'instance_deleted':
            // Remove from cache
            queryClient.setQueryData(['analyses'], (old: any[] | undefined) => {
              if (!old) return [];
              return old.filter(item => item.id !== message.data?.id);
            });
            queryClient.invalidateQueries({ queryKey: ['analyses'] });
            queryClient.invalidateQueries({ queryKey: ['model-instances'] });
            break;

          case 'pong':
            // Keep-alive response
            break;
        }
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      setIsConnected(false);
    };

    ws.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code, event.reason);
      setIsConnected(false);

      // Clear ping interval
      if (ws._pingInterval) {
        clearInterval(ws._pingInterval);
      }

      // Attempt to reconnect with exponential backoff
      if (reconnectAttempts.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
        console.log(`[WebSocket] Reconnecting in ${delay}ms...`);

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      } else {
        console.error('[WebSocket] Max reconnection attempts reached');
      }
    };

    wsRef.current = ws;
  }, [isAuthenticated, getAccessTokenSilently, queryClient]);

  useEffect(() => {
    connect();

    return () => {
      // Cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (wsRef.current) {
        if (wsRef.current._pingInterval) {
          clearInterval(wsRef.current._pingInterval);
        }
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
  };
}
