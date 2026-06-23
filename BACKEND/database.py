# BACKEND/database.py
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ruta por defecto: archivo smat.db en la raíz del proyecto
# Si este archivo está dentro de BACKEND/, ROOT_DIR será la carpeta padre (la raíz del proyecto)
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "smat.db"

# Permite sobreescribir con la variable de entorno DATABASE_URL
# Si no se proporciona, usamos la ruta por defecto (archivo sqlite en la raíz)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Normalizar DATABASE_URL:
# - Si el valor no empieza por "sqlite://", lo tratamos como una ruta de archivo y la convertimos.
# - Si el valor es una ruta relativa o absoluta sin esquema, la convertimos a sqlite:///abs_path
if not isinstance(DATABASE_URL, str):
    DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

if not DATABASE_URL.startswith("sqlite://"):
    # Si el usuario pasó una ruta de archivo (relativa o absoluta), convertirla a sqlite:///<abs_path>
    try:
        candidate = Path(DATABASE_URL)
        # Si la ruta no tiene esquema y parece relativa, resolverla respecto al ROOT_DIR
        if not candidate.is_absolute():
            candidate = (ROOT_DIR / candidate).resolve()
        DATABASE_URL = f"sqlite:///{candidate}"
    except Exception:
        # Fallback a la DB por defecto en caso de error
        DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

# Crear engine y sesión
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def ensure_event_columns():
    """
    Asegura que las columnas `pc`, `ip` y `fecha` existan en la tabla `events` (SQLite).
    Esta función es segura: no borra datos y solo intenta añadir columnas faltantes.
    """
    # Solo ejecutar si usamos SQLite (evita ejecutar PRAGMA en otras DBs)
    if not DATABASE_URL.startswith("sqlite://"):
        return

    with engine.connect() as conn:
        try:
            res = conn.exec_driver_sql("PRAGMA table_info('events')")
            rows = res.all()
            cols = [row[1] for row in rows]  # nombre de columna está en la posición 1
            # Añadir columnas faltantes de forma segura
            if 'pc' not in cols:
                conn.exec_driver_sql("ALTER TABLE events ADD COLUMN pc TEXT")
            if 'ip' not in cols:
                conn.exec_driver_sql("ALTER TABLE events ADD COLUMN ip TEXT")
            if 'fecha' not in cols:
                conn.exec_driver_sql("ALTER TABLE events ADD COLUMN fecha TEXT")
        except Exception:
            # No queremos que un fallo aquí rompa la importación del módulo
            pass

def ensure_autorizado_column():
    """
    Asegura que la columna `autorizado` exista en la tabla `events`.
    Para SQLite la representamos como INTEGER (0/1). Esta función es segura:
    - Si la columna ya existe no hace nada.
    - Si no existe, la añade con valor por defecto 1 (autorizado).
    """
    if not DATABASE_URL.startswith("sqlite://"):
        return

    with engine.connect() as conn:
        try:
            res = conn.exec_driver_sql("PRAGMA table_info('events')")
            rows = res.all()
            cols = [row[1] for row in rows]
            if 'autorizado' not in cols:
                # Añadir columna como INTEGER con valor por defecto 1
                # SQLite no soporta ADD COLUMN con DEFAULT que se aplique retroactivamente
                # pero la siguiente instrucción añade la columna; los registros existentes tendrán NULL,
                # así que actualizamos los NULL a 1 inmediatamente después.
                conn.exec_driver_sql("ALTER TABLE events ADD COLUMN autorizado INTEGER")
                conn.exec_driver_sql("UPDATE events SET autorizado = 1 WHERE autorizado IS NULL")
        except Exception:
            # Silenciar errores para no romper la importación
            pass

# Ejecutar las comprobaciones al importar el módulo (silencioso en caso de error)
try:
    ensure_event_columns()
    ensure_autorizado_column()
except Exception:
    pass
