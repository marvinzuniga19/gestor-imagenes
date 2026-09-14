import os
import sqlite3
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, send_from_directory, abort, redirect, url_for, flash
from PIL import Image, UnidentifiedImageError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gestor-imagenes-clave-secreta-2026")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

FORMATOS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "GIF": ".gif",
    "WEBP": ".webp",
}

CARPETA_IMAGENES = Path(app.instance_path) / "imagenes"
CARPETA_MINIATURAS = Path(app.instance_path) / "miniaturas"
DB_PATH = Path(app.instance_path) / "imagenes.db"

CARPETA_IMAGENES.mkdir(parents=True, exist_ok=True)
CARPETA_MINIATURAS.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def crear_miniatura(origen_path: Path, destino_path: Path, max_size=(400, 400)):
    try:
        with Image.open(origen_path) as img:
            copia = img.copy()
            if copia.mode in ("RGBA", "LA") and destino_path.suffix.lower() in (".jpg", ".jpeg"):
                fondo = Image.new("RGB", copia.size, (255, 255, 255))
                fondo.paste(copia, mask=copia.split()[-1])
                copia = fondo
            copia.thumbnail(max_size, Image.Resampling.LANCZOS)
            copia.save(destino_path, quality=85, optimize=True)
    except Exception:
        pass


def sincronizar_imagenes_existentes():
    with get_db() as conn:
        registrados = {
            row["nombre_guardado"]
            for row in conn.execute("SELECT nombre_guardado FROM imagenes")
        }
        for archivo in CARPETA_IMAGENES.iterdir():
            if archivo.is_file() and archivo.suffix.lower() in FORMATOS.values():
                miniatura_path = CARPETA_MINIATURAS / archivo.name
                if not miniatura_path.exists():
                    crear_miniatura(archivo, miniatura_path)

                if archivo.name not in registrados:
                    try:
                        with Image.open(archivo) as img:
                            ancho, alto = img.size
                    except Exception:
                        ancho, alto = None, None

                    conn.execute(
                        """
                        INSERT OR IGNORE INTO imagenes (nombre_guardado, nombre_original, tamano_bytes, ancho, alto)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (archivo.name, archivo.name, archivo.stat().st_size, ancho, alto)
                    )
        conn.commit()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS imagenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_guardado TEXT UNIQUE NOT NULL,
                nombre_original TEXT NOT NULL,
                tamano_bytes INTEGER NOT NULL,
                ancho INTEGER,
                alto INTEGER,
                fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    sincronizar_imagenes_existentes()


init_db()


@app.template_filter("tamano_legible")
def tamano_legible(bytes_count):
    if not bytes_count or bytes_count < 0:
        return "0 B"
    num = float(bytes_count)
    for unidad in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:.1f} {unidad}" if unidad != "B" else f"{int(num)} {unidad}"
        num /= 1024.0
    return f"{num:.1f} TB"


def listar_imagenes():
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, nombre_guardado, nombre_original, tamano_bytes, ancho, alto, fecha_subida
            FROM imagenes
            ORDER BY fecha_subida DESC, id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


@app.route("/")
def inicio():
    return render_template(
        "index.html",
        imagenes=listar_imagenes()
    )


@app.route("/imagenes/<nombre>")
def ver_imagen(nombre):
    return send_from_directory(CARPETA_IMAGENES, nombre)


@app.route("/miniaturas/<nombre>")
def ver_miniatura(nombre):
    ruta_miniatura = CARPETA_MINIATURAS / nombre
    if ruta_miniatura.exists() and ruta_miniatura.is_file():
        return send_from_directory(CARPETA_MINIATURAS, nombre)
    return send_from_directory(CARPETA_IMAGENES, nombre)


@app.route("/eliminar/<nombre>", methods=["POST"])
def eliminar_imagen(nombre):
    ruta = (CARPETA_IMAGENES / nombre).resolve()
    if not ruta.is_relative_to(CARPETA_IMAGENES.resolve()) or not ruta.is_file():
        abort(404)

    ruta.unlink(missing_ok=True)
    (CARPETA_MINIATURAS / nombre).unlink(missing_ok=True)

    with get_db() as conn:
        conn.execute("DELETE FROM imagenes WHERE nombre_guardado = ?", (nombre,))
        conn.commit()

    flash("Imagen eliminada correctamente.", "info")
    return redirect(url_for("inicio"))


@app.route("/subir", methods=["POST"])
def subir():
    archivo = request.files.get("imagen")

    if archivo is None or archivo.filename == "":
        flash("No seleccionaste ninguna imagen.", "error")
        return redirect(url_for("inicio"))

    nombre_original = Path(archivo.filename).name

    try:
        with Image.open(archivo.stream) as imagen:
            formato = imagen.format
            ancho, alto = imagen.size

            if formato not in FORMATOS:
                raise ValueError("Formato no permitido")

            if ancho * alto > 25_000_000:
                raise ValueError("Imagen demasiado grande")

            imagen.verify()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ):
        flash("Selecciona una imagen JPG, PNG, GIF o WebP válida.", "error")
        return redirect(url_for("inicio"))

    archivo.stream.seek(0)

    nombre_guardado = f"{uuid4().hex}{FORMATOS[formato]}"
    ruta_guardada = CARPETA_IMAGENES / nombre_guardado
    archivo.save(ruta_guardada)

    tamano_bytes = ruta_guardada.stat().st_size
    crear_miniatura(ruta_guardada, CARPETA_MINIATURAS / nombre_guardado)

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO imagenes (nombre_guardado, nombre_original, tamano_bytes, ancho, alto)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre_guardado, nombre_original, tamano_bytes, ancho, alto)
        )
        conn.commit()

    flash(f"Imagen «{nombre_original}» guardada correctamente.", "exito")
    return redirect(url_for("inicio"))


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    flash("El archivo supera el límite de 10 MB.", "error")
    return redirect(url_for("inicio")), 413


if __name__ == "__main__":
    app.run(debug=True)