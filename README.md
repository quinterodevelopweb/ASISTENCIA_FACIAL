# ASISTENCIA_FACIAL

Sistema biométrico facial con reconocimiento facial con Raspberry Pi para registro de accesos.
Proyecto Sistema embebido - Ing- de software

## Stack

- Python 3
- `face_recognition` / `dlib` para la generación de embeddings faciales (128-d)
- `opencv-python-headless` para la captura de cámara
- `customtkinter` para la interfaz gráfica
- `sqlite3` para la persistencia (usuarios, embeddings y registros de acceso)

No se almacenan imágenes de rostros: solo el embedding (vector de 128 floats)
de cada usuario, optimizado para correr en una Raspberry Pi 4.

## Flujo de asistencia (pantalla Usuario)

1. El usuario se acerca a la cámara.
2. `MotionDetector` detecta movimiento en el frame y dispara el escaneo.
3. Se genera el embedding del rostro y se compara (distancia euclidiana) contra
   los encodings activos en la BD.
4. Si no hay coincidencia: **"Usuario no identificado"** y vuelve a esperar movimiento.
5. Si el usuario es reconocido pero no está inscrito en ninguna clase:
   **"no tienes clases asignadas"**.
6. Si es reconocido y tiene clases: se muestran botones con sus clases
   (`usuario_clase`) para que elija una.
7. Al elegir: si ya tiene asistencia registrada hoy en esa clase ->
   **"La asistencia ya fue registrada hoy"**; si no, se inserta el registro en
   `asistencia` -> **"Asistencia registrada"**.

Para que un usuario pueda ser identificado y registrar asistencia debe:
estar dado de alta en `usuarios`, tener al menos un `encoding` activo, y estar
inscrito (`usuario_clase`) en al menos una clase.

## Pantallas

- **Usuario** (pantalla de inicio): solo cámara + flujo de reconocimiento de
  arriba. Tiene un botón discreto "Administrador".
- **Administrador**: protegido por contraseña (`config.settings.ADMIN_PASSWORD`,
  cambiarla antes de usar en producción). Contiene los catálogos/CRUD:
  Usuarios (alta + captura de rostro + inscripción a clases), Clases y Reportes
  (historial de asistencia). Un botón "Cerrar sesión" regresa a la pantalla Usuario.

## Estructura del proyecto

```
ASISTENCIA_FACIAL/
├── main.py                  # Punto de entrada
├── requirements.txt
├── config/
│   └── settings.py          # Rutas, cámara, reconocimiento, detección de movimiento, ADMIN_PASSWORD
├── core/
│   ├── camera.py             # Captura de video (OpenCV)
│   ├── face_encoder.py       # Generación de embeddings (face_recognition)
│   ├── face_matcher.py       # Comparación de embeddings (distancia euclidiana)
│   └── motion_detector.py    # Detección de movimiento por diferencia de frames
├── database/
│   ├── db_manager.py         # Conexión SQLite + (de)serialización de embeddings
│   └── schema.sql            # Esquema: tipo_usuario, usuarios, clases, usuario_clase, encoding, asistencia
├── services/
│   ├── usuario_service.py    # CRUD de usuarios, tipos de usuario y encodings
│   ├── clase_service.py      # CRUD de clases
│   ├── inscripcion_service.py # Inscripción usuario <-> clase (muchos a muchos)
│   └── asistencia_service.py # identificar() + registrar_asistencia()
├── gui/
│   ├── app.py                # Pantallas Usuario / Administrador (acceso por contraseña)
│   ├── widgets/
│   │   └── password_dialog.py # Diálogo modal para la contraseña de admin
│   └── views/
│       ├── base_view.py       # Hooks on_show/on_hide del ciclo de vida
│       ├── asistencia_view.py # Pantalla Usuario: cámara + reconocimiento + selección de clase
│       ├── admin_panel.py      # Sidebar del panel Administrador
│       ├── usuarios_view.py   # Alta de usuarios, captura de rostro e inscripción a clases
│       ├── clases_view.py     # Catálogo de clases
│       └── reportes_view.py   # Historial de asistencia por clase
├── utils/
│   └── logger.py
├── models/                    # Modelos de dlib (shape_predictor, resnet) - no versionados
├── data/                      # Base de datos SQLite (no versionada)
└── logs/
```

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

> En Raspberry Pi, instalar `dlib` puede tardar bastante (compilación). Se
> recomienda usar un wheel precompilado o aumentar el swap durante la instalación.
