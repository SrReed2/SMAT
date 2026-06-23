#!/usr/bin/env python
"""
Script para ejecutar el servidor SMAT en todas las interfaces (0.0.0.0:8000)
Permite que máquinas del laboratorio se conecten.
"""
import uvicorn
import os

if __name__ == "__main__":
    # Configuración: escuchar en 0.0.0.0 permite conexiones desde cualquier IP
    host = os.getenv("SMAT_HOST", "0.0.0.0")
    port = int(os.getenv("SMAT_PORT", "8000"))
    reload = os.getenv("SMAT_RELOAD", "True").lower() == "true"
    
    print(f"[SMAT] Iniciando servidor en {host}:{port}")
    print(f"[SMAT] Los agentes se conectaran a esta maquina en puerto {port}")
    
    uvicorn.run(
        "BACKEND.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

