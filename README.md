# Gestor de Imágenes 📸

Una aplicación web elegante y ligera desarrollada con **Flask** y **Pillow (PIL)** concebida como un *cuaderno digital* para subir, organizar, previsualizar y gestionar imágenes de forma segura con almacenamiento local.

---

## ✨ Características

* **Subida y validación segura**:
  * Formatos soportados: **JPEG**, **PNG**, **GIF** y **WebP**.
  * Límite de tamaño de subida de **10 MB** (`MAX_CONTENT_LENGTH`).
  * Protección contra ataques de descompresión (*Decompression Bomb*) y restricción a un máximo de 25 megapíxeles.
  * Verificación de integridad de archivos mediante **Pillow** (`Image.open` y `verify`).
  * Nombres de archivo guardados mediante identificadores UUID únicos para evitar colisiones.
* **Generación automática de miniaturas (*Thumbnails*)**:
  * Genera versiones reducidas (hasta 400×400 px) para acelerar la carga de la galería.
  * La galería muestra las miniaturas optimizadas con carga diferida (`loading="lazy"`), permitiendo abrir la imagen original a alta resolución con un solo clic.
* **Persistencia y metadatos con SQLite**:
  * Base de datos local (`instance/imagenes.db`) que almacena el nombre original del archivo, peso en disco, dimensiones (ancho × alto) y fecha de subida.
  * Auto-sincronización y migración automática de imágenes preexistentes en disco.
  * Filtro de formateo legible de tamaño (B, KB, MB, GB).
* **Experiencia de usuario moderna e interactiva**:
  * Zona de **arrastrar y soltar (*Drag & Drop*)** sobre el formulario de subida.
  * **Vista previa instantánea** del archivo seleccionado antes de subirlo, indicando nombre, tamaño y botón para descartar.
  * Patrón **Post/Redirect/Get (PRG)** con mensajes *flash* clasificados (éxito, error, advertencia) que evitan reenvíos accidentales al recargar con F5.
* **Eliminación segura**:
  * Prevención contra ataques de *Path Traversal* (`is_relative_to`).
  * Borrado en cascada del archivo original, de la miniatura y del registro en la base de datos.
* **Diseño visual editorial**:
  * Paleta cálida inspirada en papel y tinta con tipografías *Fraunces* y *Karla* de Google Fonts.
  * Diseño totalmente responsivo adaptable a dispositivos móviles y escritorios.

---

## 📁 Estructura del Proyecto

```text
gestor-imagenes/
├── main.py                   # Servidor Flask, lógica de negocio y base de datos SQLite
├── templates/
│   └── index.html            # Plantilla HTML con galería, drag & drop y vista previa
├── static/
│   └── css/
│       └── style.css         # Hoja de estilos con diseño editorial responsivo
├── instance/                 # Almacenamiento local (ignorado por Git)
│   ├── imagenes/             # Imágenes originales subidas
│   ├── miniaturas/           # Miniaturas generadas automáticamente
│   └── imagenes.db           # Base de datos SQLite con metadatos
├── .gitignore                # Reglas de exclusión para Git
└── README.md                 # Documentación del proyecto
```

---

## 🚀 Requisitos e Instalación

### Requisitos previos
* **Python 3.10** o superior.

### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd gestor-imagenes
```

### 2. Crear y activar el entorno virtual
En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install flask pillow
```

---

## ▶️ Ejecución

Para iniciar el servidor de desarrollo:
```bash
python3 main.py
```

Abre tu navegador y entra en:
```text
http://127.0.0.1:5000
```

---

## 🛡️ Variables de Entorno (Opcional)

Puedes personalizar la clave secreta de sesión configurando la variable `SECRET_KEY`:
```bash
export SECRET_KEY="tu-clave-secreta-personalizada"
python3 main.py
```

