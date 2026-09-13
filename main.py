import re
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, send_from_directory, abort, redirect, url_for
from PIL import Image, UnidentifiedImageError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

FORMATOS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "GIF": ".gif",
    "WEBP": ".webp",
}

CARPETA_IMAGENES = Path(app.instance_path) / "imagenes"
CARPETA_IMAGENES.mkdir(parents=True, exist_ok=True)


def listar_imagenes():
    archivos = [
        archivo
        for archivo in CARPETA_IMAGENES.iterdir()
        if archivo.is_file()
        and archivo.suffix.lower() in FORMATOS.values()
    ]

    archivos.sort(
        key=lambda archivo: archivo.stat().st_mtime,
        reverse=True
    )

    return [archivo.name for archivo in archivos]


@app.route("/")
def inicio():
    return render_template(
        "index.html",
        imagenes=listar_imagenes()
    )


@app.route("/imagenes/<nombre>")
def ver_imagen(nombre):
    return send_from_directory(CARPETA_IMAGENES, nombre)


@app.route("/eliminar/<nombre>", methods=["POST"])
def eliminar_imagen(nombre):
    ruta = (CARPETA_IMAGENES / nombre).resolve()
    if not ruta.is_relative_to(CARPETA_IMAGENES.resolve()) or not ruta.is_file():
        abort(404)

    ruta.unlink()
    return redirect(url_for("inicio"))


@app.route("/subir", methods=["POST"])
def subir():
    archivo = request.files.get("imagen")

    if archivo is None or archivo.filename == "":
        return render_template(
            "index.html",
            mensaje="No seleccionaste ninguna imagen.",
            imagenes=listar_imagenes()
        )

    try:
        with Image.open(archivo.stream) as imagen:
            formato = imagen.format

            if formato not in FORMATOS:
                raise ValueError("Formato no permitido")

            if imagen.width * imagen.height > 25_000_000:
                raise ValueError("Imagen demasiado grande")

            imagen.verify()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ):
        return render_template(
            "index.html",
            mensaje="Selecciona una imagen JPG, PNG, GIF o WebP válida.",
            imagenes=listar_imagenes()
        )

    archivo.stream.seek(0)

    nombre_guardado = f"{uuid4().hex}{FORMATOS[formato]}"
    archivo.save(CARPETA_IMAGENES / nombre_guardado)

    return render_template(
        "index.html",
        mensaje=f"Imagen guardada correctamente: {nombre_guardado}",
        imagenes=listar_imagenes()
    )


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    return render_template(
        "index.html",
        mensaje="El archivo supera el límite de 10 MB.",
        imagenes=listar_imagenes()
    ), 413


if __name__ == "__main__":
    app.run(debug=True)