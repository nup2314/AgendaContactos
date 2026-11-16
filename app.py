import os
import re
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, session)
from werkzeug.security import generate_password_hash, check_password_hash

from database import obtener_conexion, crear_tabla, ErrorIntegridad
from iconos import ICONOS, EMOJIS

app = Flask(__name__)
# Firma la sesión (la "cookie" que recuerda quién inició sesión).
# En Render se toma de la variable de entorno SECRET_KEY (larga, aleatoria y secreta).
EN_RENDER = bool(os.environ.get("RENDER"))
CLAVE = os.environ.get("SECRET_KEY")
if EN_RENDER and not CLAVE:
    raise RuntimeError("Falta la variable de entorno SECRET_KEY en Render.")
app.secret_key = CLAVE or "cambia-esta-clave-en-tu-proyecto"

# Cookie de sesión más segura. SECURE solo en Render (usa HTTPS).
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = EN_RENDER

# Crea las tablas al iniciar la aplicación.
crear_tabla()

# Reglas para crear una cuenta.
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9_]{3,20}$")
LARGO_MINIMO_CLAVE = 8


# Hace que ICONOS y EMOJIS estén disponibles en todas las plantillas.
@app.context_processor
def datos_globales():
    return {"ICONOS": ICONOS, "EMOJIS": EMOJIS}


# ---------- PROTECCIÓN DE RUTAS ----------
def login_requerido(funcion):
    """Si no hay sesión iniciada, manda al usuario a /login."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Inicia sesión para entrar a tu libro de aldeanos.")
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return envoltura


# ---------- CUENTAS: REGISTRO, LOGIN Y LOGOUT ----------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "")
        confirmar = request.form.get("confirmar", "")

        # Validación del lado del servidor.
        error = None
        if not PATRON_USUARIO.match(usuario):
            error = "El usuario debe tener de 3 a 20 letras, números o guion bajo (_)."
        elif len(clave) < LARGO_MINIMO_CLAVE:
            error = f"La contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres."
        elif clave != confirmar:
            error = "Las contraseñas no coinciden."

        if error:
            flash(error)
            return redirect(url_for("registro"))

        conexion = obtener_conexion()
        try:
            conexion.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                (usuario, generate_password_hash(clave))
            )
            nuevo_id = conexion.execute(
                "SELECT id FROM usuarios WHERE LOWER(usuario) = LOWER(?)", (usuario,)
            ).fetchone()["id"]

            # Si es la primera cuenta, adopta los contactos creados antes
            # de que existieran los usuarios (para no perderlos).
            total = conexion.execute(
                "SELECT COUNT(*) AS total FROM usuarios"
            ).fetchone()["total"]
            if total == 1:
                conexion.execute(
                    "UPDATE contactos SET usuario_id = ? WHERE usuario_id IS NULL",
                    (nuevo_id,)
                )
            conexion.commit()
        except ErrorIntegridad:
            # El índice de usuario es único: ya existe ese nombre.
            conexion.close()
            flash("Ese nombre de usuario ya está en uso. Elige otro.")
            return redirect(url_for("registro"))
        conexion.close()

        # Inicia sesión automáticamente con la cuenta nueva.
        session.clear()
        session["usuario_id"] = nuevo_id
        session["usuario"] = usuario
        flash("¡Cuenta creada! Bienvenido a tu libro de aldeanos.")
        return redirect(url_for("inicio"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "")

        conexion = obtener_conexion()
        fila = conexion.execute(
            "SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(?)", (usuario,)
        ).fetchone()
        conexion.close()

        # Mismo mensaje si falla el usuario o la contraseña:
        # así no se revela qué usuarios existen.
        if fila is None or not check_password_hash(fila["password_hash"], clave):
            flash("Usuario o contraseña incorrectos.")
            return redirect(url_for("login"))

        session.clear()
        session["usuario_id"] = fila["id"]
        session["usuario"] = fila["usuario"]
        flash(f"¡Bienvenido de nuevo, {fila['usuario']}!")
        return redirect(url_for("inicio"))

    return render_template("login.html")


# Cerrar sesión se hace con POST para que un enlace ajeno no pueda forzarlo.
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada. ¡Hasta pronto!")
    return redirect(url_for("login"))


# ---------- CRUD (cada usuario solo ve y modifica SUS contactos) ----------
# READ
@app.route("/")
@login_requerido
def inicio():
    conexion = obtener_conexion()
    contactos = conexion.execute(
        "SELECT * FROM contactos WHERE usuario_id = ? ORDER BY nombre",
        (session["usuario_id"],)
    ).fetchall()
    conexion.close()
    return render_template("index.html", contactos=contactos)


# CREATE
@app.route("/agregar", methods=["POST"])
@login_requerido
def agregar():
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip()
    categoria = request.form.get("categoria", "").strip()

    if not nombre or not telefono or not categoria:
        flash("Completa los campos obligatorios.")
        return redirect(url_for("inicio"))

    conexion = obtener_conexion()
    conexion.execute(
        """
        INSERT INTO contactos (nombre, telefono, correo, categoria, usuario_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nombre, telefono, correo, categoria, session["usuario_id"])
    )
    conexion.commit()
    conexion.close()

    flash("¡Contacto guardado correctamente!")
    return redirect(url_for("inicio"))


# UPDATE
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_requerido
def editar(id):
    conexion = obtener_conexion()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        categoria = request.form.get("categoria", "").strip()

        if not nombre or not telefono or not categoria:
            conexion.close()
            flash("Completa los campos obligatorios.")
            return redirect(url_for("editar", id=id))

        # AND usuario_id = ? evita editar contactos de otra persona.
        conexion.execute(
            """
            UPDATE contactos
            SET nombre = ?, telefono = ?, correo = ?, categoria = ?
            WHERE id = ? AND usuario_id = ?
            """,
            (nombre, telefono, correo, categoria, id, session["usuario_id"])
        )
        conexion.commit()
        conexion.close()
        flash("Contacto actualizado.")
        return redirect(url_for("inicio"))

    contacto = conexion.execute(
        "SELECT * FROM contactos WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"])
    ).fetchone()
    conexion.close()

    if contacto is None:
        flash("El contacto no existe.")
        return redirect(url_for("inicio"))

    return render_template("editar.html", contacto=contacto)


# DELETE
@app.route("/eliminar/<int:id>", methods=["POST"])
@login_requerido
def eliminar(id):
    conexion = obtener_conexion()
    conexion.execute(
        "DELETE FROM contactos WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"])
    )
    conexion.commit()
    conexion.close()
    flash("Contacto eliminado.")
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    # Solo para trabajar en tu computadora. Render usa gunicorn (ver requirements.txt).
    app.run(debug=True)
