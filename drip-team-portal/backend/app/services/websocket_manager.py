"""
WebSocket Connection Manager for Real-Time Analysis Updates

Manages WebSocket connections and broadcasts analysis changes to connected clients.
Supports multiple connection types:
- Global listeners (receive all analysis updates)
- Analysis-specific listeners (receive updates for specific analyses)
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time analysis updates.

    Usage:
        manager = ConnectionManager()

        # In WebSocket endpoint:
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages (e.g., subscribe to specific analysis)
        except WebSocketDisconnect:
            manager.disconnect(websocket)

        # When analysis changes:
        await manager.broadcast_analysis_update(analysis_id, data)
    """

    def __init__(self):
        # All active connections
        self.active_connections: Set[WebSocket] = set()

        # Connections subscribed to specific analyses
        # Key: analysis_id, Value: set of WebSocket connections
        self.analysis_subscriptions: Dict[int, Set[WebSocket]] = {}

        # Reverse mapping for efficient cleanup
        # Key: WebSocket, Value: set of analysis_ids
        self.connection_subscriptions: Dict[WebSocket, Set[int]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_subscriptions[websocket] = set()
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and clean up subscriptions."""
        # Remove from active connections
        self.active_connections.discard(websocket)

        # Clean up analysis subscriptions
        if websocket in self.connection_subscriptions:
            for analysis_id in self.connection_subscriptions[websocket]:
                if analysis_id in self.analysis_subscriptions:
                    self.analysis_subscriptions[analysis_id].discard(websocket)
                    # Clean up empty subscription sets
                    if not self.analysis_subscriptions[analysis_id]:
                        del self.analysis_subscriptions[analysis_id]
            del self.connection_subscriptions[websocket]

        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    def subscribe_to_analysis(self, websocket: WebSocket, analysis_id: int) -> None:
        """Subscribe a connection to updates for a specific analysis."""
        if analysis_id not in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id] = set()
        self.analysis_subscriptions[analysis_id].add(websocket)

        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].add(analysis_id)

        logger.debug(f"WebSocket subscribed to analysis {analysis_id}")

    def unsubscribe_from_analysis(self, websocket: WebSocket, analysis_id: int) -> None:
        """Unsubscribe a connection from a specific analysis."""
        if analysis_id in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id].discard(websocket)
            if not self.analysis_subscriptions[analysis_id]:
                del self.analysis_subscriptions[analysis_id]

        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].discard(analysis_id)

        logger.debug(f"WebSocket unsubscribed from analysis {analysis_id}")

    async def broadcast_to_all(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        message_text = json.dumps(message)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_analysis_update(
        self,
        analysis_id: int,
        event_type: str,
        data: dict
    ) -> None:
        """
        Broadcast an analysis update to:
        1. All global listeners
        2. Connections subscribed to this specific analysis

        Args:
            analysis_id: The ID of the analysis that changed
            event_type: Type of event (created, updated, deleted, evaluated)
            data: The analysis data to broadcast
        """
        message = {
            "type": "analysis_update",
            "event": event_type,
            "analysis_id": analysis_id,
            "data": data
        }

        # Get unique set of connections to notify
        connections_to_notify: Set[WebSocket] = set()

        # Add all active connections (global listeners)
        connections_to_notify.update(self.active_connections)

        # Add analysis-specific subscribers (they're already in active_connections,
        # but this ensures we don't miss any edge cases)
        if analysis_id in self.analysis_subscriptions:
            connections_to_notify.update(self.analysis_subscriptions[analysis_id])

        if not connections_to_notify:
            return

        message_text = json.dumps(message)
        disconnected = []

        for connection in connections_to_notify:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.warning(f"Failed to broadcast analysis update: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

        logger.info(f"Broadcast analysis {event_type} for ID {analysis_id} to {len(connections_to_notify)} clients")

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_subscription_count(self, analysis_id: int) -> int:
        """Get the number of subscribers for a specific analysis."""
        return len(self.analysis_subscriptions.get(analysis_id, set()))


# Global instance for use across the application
manager = ConnectionManager()
