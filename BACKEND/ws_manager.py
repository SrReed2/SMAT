# BACKEND/ws_manager.py
import asyncio
import json
from typing import Set
from fastapi import WebSocket

_connections: Set[WebSocket] = set()
_connections_lock = asyncio.Lock()

async def register(ws: WebSocket):
    """Registrar una conexión WebSocket."""
    async with _connections_lock:
        _connections.add(ws)

async def unregister(ws: WebSocket):
    """Eliminar una conexión WebSocket."""
    async with _connections_lock:
        if ws in _connections:
            _connections.remove(ws)

async def broadcast(event: dict):
    """
    Enviar (broadcast) un evento JSON a todas las conexiones WebSocket activas.
    Si alguna conexión falla, se elimina de la lista.
    """
    text = json.dumps(event)
    to_remove = []
    async with _connections_lock:
        conns = list(_connections)
    for conn in conns:
        try:
            await conn.send_text(text)
        except Exception:
            to_remove.append(conn)

    if to_remove:
        async with _connections_lock:
            for c in to_remove:
                if c in _connections:
                    _connections.remove(c)
