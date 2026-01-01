"""
WebSocket Endpoint for Real-Time Analysis Updates

Provides real-time notifications when analyses are created, updated, deleted, or evaluated.

Client Connection:
    ws://localhost:8000/ws/analyses

Message Protocol:
    Incoming (client -> server):
        {"action": "subscribe", "analysis_id": 123}
        {"action": "unsubscribe", "analysis_id": 123}
        {"action": "ping"}

    Outgoing (server -> client):
        {
            "type": "analysis_update",
            "event": "created|updated|deleted|evaluated",
            "analysis_id": 123,
            "data": {...analysis data...}
        }
        {"type": "pong"}
        {"type": "error", "message": "..."}
        {"type": "subscribed", "analysis_id": 123}
        {"type": "unsubscribed", "analysis_id": 123}
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/analyses")
async def websocket_analyses(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis updates.

    All connected clients receive updates when any analysis changes.
    Clients can also subscribe to specific analyses for targeted updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive and parse message
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "ping":
                    # Heartbeat/keepalive
                    await manager.send_personal_message(websocket, {"type": "pong"})

                elif action == "subscribe":
                    # Subscribe to a specific analysis
                    analysis_id = message.get("analysis_id")
                    if analysis_id is not None:
                        manager.subscribe_to_analysis(websocket, int(analysis_id))
                        await manager.send_personal_message(websocket, {
                            "type": "subscribed",
                            "analysis_id": analysis_id
                        })
                    else:
                        await manager.send_personal_message(websocket, {
                            "type": "error",
                            "message": "analysis_id required for subscribe action"
                        })

                elif action == "unsubscribe":
                    # Unsubscribe from a specific analysis
                    analysis_id = message.get("analysis_id")
                    if analysis_id is not None:
                        manager.unsubscribe_from_analysis(websocket, int(analysis_id))
                        await manager.send_personal_message(websocket, {
                            "type": "unsubscribed",
                            "analysis_id": analysis_id
                        })
                    else:
                        await manager.send_personal_message(websocket, {
                            "type": "error",
                            "message": "analysis_id required for unsubscribe action"
                        })

                else:
                    await manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })

            except json.JSONDecodeError:
                await manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
