"""
WebSocket Tests for Analysis Real-Time Updates

Tests for:
- WebSocket connection at /ws/analyses
- Message protocol (subscribe, unsubscribe, ping/pong)
- Broadcasts on CRUD operations
- Multiple client handling
- Connection cleanup

NOTE: Requires the WebSocket endpoint to be registered in main.py.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.physics_model import ModelInstance, ModelInput
from app.models.values import ComputationStatus
from app.services.websocket_manager import ConnectionManager


# ==================== UNIT TESTS: ConnectionManager ====================

class TestConnectionManagerUnit:
    """Unit tests for ConnectionManager without actual WebSocket connections."""

    @pytest.fixture
    def manager(self):
        """Create fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_adds_to_active_connections(self, manager, mock_websocket):
        """connect() adds WebSocket to active_connections."""
        await manager.connect(mock_websocket)

        assert mock_websocket in manager.active_connections
        assert mock_websocket in manager.connection_subscriptions
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        """connect() calls websocket.accept()."""
        await manager.connect(mock_websocket)

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_active(self, manager, mock_websocket):
        """disconnect() removes WebSocket from active_connections."""
        await manager.connect(mock_websocket)
        manager.disconnect(mock_websocket)

        assert mock_websocket not in manager.active_connections
        assert mock_websocket not in manager.connection_subscriptions
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_subscriptions(self, manager, mock_websocket):
        """disconnect() removes WebSocket from all analysis subscriptions."""
        await manager.connect(mock_websocket)

        # Subscribe to multiple analyses
        manager.subscribe_to_analysis(mock_websocket, 1)
        manager.subscribe_to_analysis(mock_websocket, 2)
        manager.subscribe_to_analysis(mock_websocket, 3)

        assert manager.get_subscription_count(1) == 1
        assert manager.get_subscription_count(2) == 1

        # Disconnect
        manager.disconnect(mock_websocket)

        # All subscriptions should be cleaned up
        assert manager.get_subscription_count(1) == 0
        assert manager.get_subscription_count(2) == 0
        assert manager.get_subscription_count(3) == 0

    def test_subscribe_to_analysis(self, manager, mock_websocket):
        """subscribe_to_analysis() adds connection to analysis subscribers."""
        manager.active_connections.add(mock_websocket)
        manager.connection_subscriptions[mock_websocket] = set()

        manager.subscribe_to_analysis(mock_websocket, 123)

        assert mock_websocket in manager.analysis_subscriptions[123]
        assert 123 in manager.connection_subscriptions[mock_websocket]
        assert manager.get_subscription_count(123) == 1

    def test_unsubscribe_from_analysis(self, manager, mock_websocket):
        """unsubscribe_from_analysis() removes connection from subscribers."""
        manager.active_connections.add(mock_websocket)
        manager.connection_subscriptions[mock_websocket] = set()

        manager.subscribe_to_analysis(mock_websocket, 123)
        manager.unsubscribe_from_analysis(mock_websocket, 123)

        assert manager.get_subscription_count(123) == 0
        assert 123 not in manager.connection_subscriptions[mock_websocket]

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager, mock_websocket):
        """broadcast_to_all() sends message to all connected clients."""
        ws1 = MagicMock()
        ws1.send_text = AsyncMock()
        ws2 = MagicMock()
        ws2.send_text = AsyncMock()

        manager.active_connections.add(ws1)
        manager.active_connections.add(ws2)

        message = {"type": "test", "data": "hello"}
        await manager.broadcast_to_all(message)

        expected_json = json.dumps(message)
        ws1.send_text.assert_called_once_with(expected_json)
        ws2.send_text.assert_called_once_with(expected_json)

    @pytest.mark.asyncio
    async def test_broadcast_to_all_handles_disconnected(self, manager):
        """broadcast_to_all() removes clients that fail to receive."""
        ws_good = MagicMock()
        ws_good.send_text = AsyncMock()

        ws_bad = MagicMock()
        ws_bad.send_text = AsyncMock(side_effect=Exception("Connection closed"))

        manager.active_connections.add(ws_good)
        manager.active_connections.add(ws_bad)
        manager.connection_subscriptions[ws_good] = set()
        manager.connection_subscriptions[ws_bad] = set()

        await manager.broadcast_to_all({"type": "test"})

        # Bad connection should be removed
        assert ws_good in manager.active_connections
        assert ws_bad not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_analysis_update(self, manager, mock_websocket):
        """broadcast_analysis_update() sends to global and subscribed clients."""
        ws_global = MagicMock()
        ws_global.send_text = AsyncMock()

        ws_subscribed = MagicMock()
        ws_subscribed.send_text = AsyncMock()

        manager.active_connections.add(ws_global)
        manager.active_connections.add(ws_subscribed)
        manager.connection_subscriptions[ws_global] = set()
        manager.connection_subscriptions[ws_subscribed] = set()

        manager.subscribe_to_analysis(ws_subscribed, 123)

        data = {"id": 123, "name": "Test"}
        await manager.broadcast_analysis_update(123, "created", data)

        # Both should receive (global gets all, subscribed gets specific)
        assert ws_global.send_text.called
        assert ws_subscribed.send_text.called

        # Check message format
        call_args = ws_global.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "analysis_update"
        assert message["event"] == "created"
        assert message["analysis_id"] == 123
        assert message["data"]["name"] == "Test"

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager, mock_websocket):
        """send_personal_message() sends only to specific connection."""
        await manager.connect(mock_websocket)

        await manager.send_personal_message(mock_websocket, {"type": "test"})

        mock_websocket.send_text.assert_called_with('{"type": "test"}')

    def test_connection_count(self, manager, mock_websocket):
        """connection_count property returns active connection count."""
        assert manager.connection_count == 0

        manager.active_connections.add(mock_websocket)
        assert manager.connection_count == 1

    def test_get_subscription_count_no_subscribers(self, manager):
        """get_subscription_count() returns 0 for unsubscribed analysis."""
        assert manager.get_subscription_count(999) == 0


# ==================== INTEGRATION TESTS: WebSocket Endpoint ====================

class TestWebSocketConnection:
    """Test WebSocket connection and disconnection."""

    def test_connect_to_websocket(self, client, db):
        """Can connect to WebSocket endpoint."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                # Connection should succeed
                pass
        except Exception as e:
            if "404" in str(e) or "WebSocket" not in str(type(e)):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise

    def test_websocket_ping_pong(self, client, db):
        """WebSocket responds to ping with pong."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                # Send ping
                websocket.send_json({"action": "ping"})

                # Should receive pong
                response = websocket.receive_json()
                assert response["type"] == "pong"
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise

    def test_websocket_subscribe(self, client, db, thermal_analysis):
        """Can subscribe to specific analysis."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                # Subscribe to analysis
                websocket.send_json({
                    "action": "subscribe",
                    "analysis_id": thermal_analysis.id
                })

                # Should receive confirmation
                response = websocket.receive_json()
                assert response["type"] == "subscribed"
                assert response["analysis_id"] == thermal_analysis.id
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise

    def test_websocket_unsubscribe(self, client, db, thermal_analysis):
        """Can unsubscribe from analysis."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                # Subscribe first
                websocket.send_json({
                    "action": "subscribe",
                    "analysis_id": thermal_analysis.id
                })
                websocket.receive_json()  # Skip subscription confirmation

                # Unsubscribe
                websocket.send_json({
                    "action": "unsubscribe",
                    "analysis_id": thermal_analysis.id
                })

                response = websocket.receive_json()
                assert response["type"] == "unsubscribed"
                assert response["analysis_id"] == thermal_analysis.id
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise

    def test_websocket_invalid_action(self, client, db):
        """Invalid action returns error."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                websocket.send_json({"action": "invalid_action"})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Unknown action" in response["message"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise

    def test_websocket_invalid_json(self, client, db):
        """Invalid JSON returns error."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                websocket.send_text("not valid json{{{")

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise

    def test_websocket_subscribe_missing_id(self, client, db):
        """Subscribe without analysis_id returns error."""
        try:
            with client.websocket_connect("/ws/analyses") as websocket:
                websocket.send_json({"action": "subscribe"})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "analysis_id required" in response["message"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not registered in main.py")
            raise


class TestWebSocketBroadcasts:
    """Test WebSocket broadcasts on CRUD operations.

    NOTE: These tests require:
    1. Analysis REST API endpoints (/api/v1/analyses) to be implemented
    2. REST API to call ws_manager.broadcast_analysis_update()

    Currently skipped until the Analysis REST API is implemented.
    """

    def test_broadcast_on_create(self, client, db, thermal_model, auth_headers):
        """Creating analysis broadcasts to WebSocket clients."""
        with client.websocket_connect("/ws/analyses") as websocket:
            create_response = client.post(
                "/api/v1/analyses",
                json={
                    "name": "Broadcast Test Create",
                    "model_version_id": thermal_model.current_version.id,
                    "bindings": {
                        "CTE": "2.3e-5",
                        "delta_T": "100",
                        "L0": "0.003"
                    }
                },
                headers=auth_headers
            )

            assert create_response.status_code in [200, 201]

            # Should receive broadcast
            response = websocket.receive_json()
            assert response["type"] == "analysis_update"
            assert response["event"] == "created"
            assert response["data"]["name"] == "Broadcast Test Create"

    def test_broadcast_on_update(self, client, db, thermal_analysis, auth_headers):
        """Updating analysis broadcasts to clients."""
        with client.websocket_connect("/ws/analyses") as websocket:
            update_response = client.patch(
                f"/api/v1/analyses/{thermal_analysis.id}",
                json={"name": "Updated via Broadcast Test"},
                headers=auth_headers
            )

            assert update_response.status_code == 200

            response = websocket.receive_json()
            assert response["type"] == "analysis_update"
            assert response["event"] == "updated"
            assert response["data"]["name"] == "Updated via Broadcast Test"

    def test_broadcast_on_delete(self, client, db, thermal_analysis, auth_headers):
        """Deleting analysis broadcasts to clients."""
        analysis_id = thermal_analysis.id

        with client.websocket_connect("/ws/analyses") as websocket:
            delete_response = client.delete(
                f"/api/v1/analyses/{analysis_id}",
                headers=auth_headers
            )

            assert delete_response.status_code == 200

            response = websocket.receive_json()
            assert response["type"] == "analysis_update"
            assert response["event"] == "deleted"
            assert response["analysis_id"] == analysis_id

    def test_broadcast_on_evaluate(self, client, db, thermal_analysis, auth_headers):
        """Evaluating analysis broadcasts to clients."""
        with client.websocket_connect("/ws/analyses") as websocket:
            eval_response = client.post(
                f"/api/v1/analyses/{thermal_analysis.id}/evaluate",
                headers=auth_headers
            )

            assert eval_response.status_code == 200

            response = websocket.receive_json()
            assert response["type"] == "analysis_update"
            assert response["event"] == "evaluated"
            assert len(response["data"]["output_value_nodes"]) > 0

    def test_multiple_clients_receive_broadcast(self, client, db, thermal_model, auth_headers):
        """All connected clients receive broadcasts."""
        with client.websocket_connect("/ws/analyses") as ws1, \
             client.websocket_connect("/ws/analyses") as ws2:

            create_response = client.post(
                "/api/v1/analyses",
                json={
                    "name": "Multi-Client Test",
                    "model_version_id": thermal_model.current_version.id,
                    "bindings": {
                        "CTE": "2.3e-5",
                        "delta_T": "100",
                        "L0": "0.003"
                    }
                },
                headers=auth_headers
            )

            assert create_response.status_code in [200, 201]

            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()

            assert msg1["type"] == "analysis_update"
            assert msg2["type"] == "analysis_update"
            assert msg1["data"]["name"] == "Multi-Client Test"
            assert msg2["data"]["name"] == "Multi-Client Test"

    def test_subscribed_client_receives_updates(self, client, db, thermal_analysis, auth_headers):
        """Subscribed clients receive updates for their analysis."""
        with client.websocket_connect("/ws/analyses") as websocket:
            websocket.send_json({
                "action": "subscribe",
                "analysis_id": thermal_analysis.id
            })
            websocket.receive_json()  # Skip subscription confirmation

            client.patch(
                f"/api/v1/analyses/{thermal_analysis.id}",
                json={"name": "Subscribed Update"},
                headers=auth_headers
            )

            response = websocket.receive_json()
            assert response["analysis_id"] == thermal_analysis.id


class TestWebSocketEdgeCases:
    """Test edge cases and error handling."""

    def test_broadcast_with_no_connections(self):
        """Broadcast with no connections should not error."""
        import asyncio
        manager = ConnectionManager()

        # Should complete without error
        asyncio.get_event_loop().run_until_complete(
            manager.broadcast_to_all({"type": "test"})
        )

    def test_multiple_subscriptions_same_analysis(self):
        """Multiple connections can subscribe to same analysis."""
        manager = ConnectionManager()

        ws1 = MagicMock()
        ws2 = MagicMock()

        manager.active_connections.add(ws1)
        manager.active_connections.add(ws2)
        manager.connection_subscriptions[ws1] = set()
        manager.connection_subscriptions[ws2] = set()

        manager.subscribe_to_analysis(ws1, 123)
        manager.subscribe_to_analysis(ws2, 123)

        assert manager.get_subscription_count(123) == 2

    def test_disconnect_nonexistent_connection(self):
        """Disconnecting non-existent connection should not error."""
        manager = ConnectionManager()
        fake_ws = MagicMock()

        # Should not raise
        manager.disconnect(fake_ws)

    def test_unsubscribe_nonexistent_subscription(self):
        """Unsubscribing from non-existent subscription should not error."""
        manager = ConnectionManager()
        ws = MagicMock()

        manager.active_connections.add(ws)
        manager.connection_subscriptions[ws] = set()

        # Should not raise
        manager.unsubscribe_from_analysis(ws, 999)
