# ============================================================
#  ICONOS DE LA AGENDA
#  Pega aquí el LINK de cada imagen entre las comillas.
#  Los iconos se ajustan solos al tamaño del texto.
#
#  Puedes usar:
#    1) Un link de internet:   "https://sitio.com/espada.png"
#    2) Un archivo local: guarda la imagen en static/img/
#       y escribe:             "img/espada.png"
#
#  Si dejas un espacio vacío ("") se muestra el emoji de respaldo.
# ============================================================

ICONOS = {
    # --- Encabezado ---
    "titulo_izq": "",      # icono a la izquierda del título
    "titulo_der": "",      # icono a la derecha del título

    # --- Tarjetas ---
    "nuevo": "",           # título "Nuevo aldeano"
    "lista": "",           # título "Aldeanos registrados"

    # --- Campos del formulario ---
    "nombre": "",
    "telefono": "",
    "correo": "",
    "categoria": "",

    # --- Cuenta (inicio de sesión y registro) ---
    "usuario": "",         # campo de usuario y barra superior
    "clave": "",           # campos de contraseña
    "entrar": "",          # botón "Iniciar sesión"
    "registro": "",        # botón y título "Crear cuenta"
    "salir": "",           # botón "Cerrar sesión"

    # --- Botones ---
    "guardar": "",
    "editar": "",
    "eliminar": "",

    # --- Categorías (aparecen en la tabla) ---
    "cat_Familia": "",
    "cat_Escuela": "",
    "cat_Trabajo": "",
    "cat_Otro": "",

    # --- Otros ---
    "mensaje": "",         # avisos de "guardado", "eliminado", etc.
    "vacio": "",           # cuando no hay contactos
    "pie": "",             # a los lados del texto del pie de página
}

# Emojis que se usan cuando el espacio de arriba está vacío.
EMOJIS = {
    "titulo_izq": "⛏️", "titulo_der": "📖",
    "nuevo": "🪓", "lista": "🗺️",
    "usuario": "🧑", "clave": "🔑", "entrar": "🚪", "registro": "📜", "salir": "🛏️",
    "nombre": "👤", "telefono": "📞", "correo": "✉️", "categoria": "🧭",
    "guardar": "💎", "editar": "🗡️", "eliminar": "🧨",
    "cat_Familia": "🏠", "cat_Escuela": "📖", "cat_Trabajo": "⛏️", "cat_Otro": "🧭",
    "mensaje": "💎", "vacio": "🌱", "pie": "🧱",
}
