import os
import sqlite3

# Si existe la variable DATABASE_URL (en Render) se usa PostgreSQL (Neon).
# Si no existe (en tu computadora) se usa el archivo SQLite contactos.db.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USA_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))

if USA_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
    ErrorIntegridad = (sqlite3.IntegrityError, psycopg.IntegrityError)
else:
    ErrorIntegridad = (sqlite3.IntegrityError,)


class Conexion:
    """Envuelve la conexión para que app.py funcione igual con SQLite y PostgreSQL."""

    def __init__(self, conexion):
        self._conexion = conexion

    def execute(self, sql, parametros=()):
        # SQLite usa ? como marcador y PostgreSQL usa %s.
        if USA_POSTGRES:
            sql = sql.replace("?", "%s")
        return self._conexion.execute(sql, parametros)

    def commit(self):
        self._conexion.commit()

    def close(self):
        self._conexion.close()


def obtener_conexion():
    if USA_POSTGRES:
        # prepare_threshold=None: compatible con las conexiones "pooled" de Neon.
        conexion = psycopg.connect(DATABASE_URL, row_factory=dict_row,
                                   prepare_threshold=None)
    else:
        # Abre la base de datos. Si no existe, SQLite la crea.
        conexion = sqlite3.connect("contactos.db")
        # Permite acceder a las columnas por su nombre.
        conexion.row_factory = sqlite3.Row
    return Conexion(conexion)


def crear_tabla():
    conexion = obtener_conexion()

    # Identificador automático: cambia la sintaxis según la base de datos.
    id_auto = "SERIAL PRIMARY KEY" if USA_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

    # Tabla de usuarios: guarda el HASH de la contraseña, nunca la contraseña.
    conexion.execute(f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id {id_auto},
            usuario TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # Índice único sin distinguir mayúsculas: "Steve" y "steve" son el mismo usuario.
    conexion.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS usuarios_usuario_ci ON usuarios (LOWER(usuario))"
    )

    # Tabla de contactos: cada contacto pertenece a un usuario.
    conexion.execute(f"""
        CREATE TABLE IF NOT EXISTS contactos (
            id {id_auto},
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            correo TEXT,
            categoria TEXT NOT NULL,
            usuario_id INTEGER REFERENCES usuarios(id)
        )
    """)

    # Solo SQLite: si la base es de una versión anterior (sin usuario_id),
    # agrega la columna sin perder los contactos que ya existían.
    if not USA_POSTGRES:
        columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(contactos)")]
        if "usuario_id" not in columnas:
            conexion.execute(
                "ALTER TABLE contactos ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"
            )

    conexion.commit()
    conexion.close()
