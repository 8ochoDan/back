```text
object-recognition/
│
├── frontend/        ← Next.js + React
│
└── backend/         ← Python + FastAPI
    ├── app/
    │   ├── main.py
    │   ├── api/
    │   ├── models/
    │   ├── services/
    │   └── core/
    │
    ├── models/
    ├── tests/
    ├── requirements.txt
    └── .env
```

El flujo será:

```text
┌─────────────────────┐
│ Next.js + React     │
│ Interfaz web        │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│ FastAPI             │
│ Backend             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ TensorFlow.js /     │
│ TensorFlow +        │
│ COCO-SSD            │
└──────────┬──────────┘
           │
           ▼
      Detecciones
      ├── clase
      ├── confianza
      └── bounding box
```

Hay una aclaración importante antes de instalar: **COCO-SSD es originalmente un modelo/ecosistema muy utilizado con TensorFlow.js**. Si quieres ejecutarlo directamente dentro de Python, no conviene asumir que el paquete de `@tensorflow-models/coco-ssd` se instala como una librería Python normal. Para un backend Python, hay que elegir una implementación/modelo compatible con TensorFlow Python o utilizar TensorFlow.js de una manera distinta. Te dejo abajo la instalación base de FastAPI y el entorno preparado, y luego podemos montar la parte exacta de COCO-SSD sin mezclar tecnologías.

# 1. Crear la carpeta del proyecto

Si ya tienes tu proyecto frontend, puedes dejarlo así:

```text
object-recognition/
├── frontend/
└── backend/
```

Desde PowerShell:

```powershell
mkdir object-recognition
cd object-recognition

mkdir backend
cd backend
```

----------

# 2. Comprobar Python

Ejecuta:

```powershell
python --version
```

o:

```powershell
py --version
```

Te recomiendo utilizar una versión de Python compatible con la versión de TensorFlow que vayamos a utilizar, en lugar de instalar la versión más nueva a ciegas.

Por ejemplo, si tienes:

```text
Python 3.11.x
```

es una buena base para este proyecto.

----------

# 3. Crear un entorno virtual

Dentro de:

```text
object-recognition/backend/
```

ejecuta:

```powershell
python -m venv .venv
```

Actívalo:

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución, puedes permitir scripts para tu usuario:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Después:

```powershell
.venv\Scripts\Activate.ps1
```

Deberías ver algo parecido a:

```text
(.venv) PS C:\...\object-recognition\backend>
```

Eso significa que estás trabajando dentro del entorno virtual.

----------

# 4. Actualizar pip

```powershell
python -m pip install --upgrade pip
```

----------

# 5. Instalar FastAPI

Instala FastAPI y Uvicorn:

```powershell
pip install fastapi uvicorn[standard]
```

FastAPI será nuestro framework:

```text
POST /recognize
GET  /health
```

y Uvicorn será el servidor que ejecutará la aplicación.

----------

# 6. Instalar procesamiento de imágenes

Para nuestro sistema vamos a necesitar recibir imágenes desde Next.js y procesarlas.

Instala Pillow:

```powershell
pip install pillow
```

Posteriormente nos permitirá convertir:

```text
Upload
   ↓
bytes
   ↓
PIL.Image
   ↓
Tensor
   ↓
Modelo
```

----------

# 7. Instalar NumPy

```powershell
pip install numpy
```

Lo necesitaremos para transformar las imágenes a matrices que puedan procesar los modelos de TensorFlow.

----------

# 8. Instalar TensorFlow

Aquí hay que tener un poco de cuidado porque la versión de Python y la plataforma importan.

Primero puedes intentar:

```powershell
pip install tensorflow
```

Después:

```powershell
python -c "import tensorflow as tf; print(tf.__version__)"
```

Si funciona deberías obtener algo como:

```text
2.x.x
```

También puedes comprobar:

```powershell
python -c "import tensorflow as tf; print(tf.config.list_physical_devices())"
```

----------

# 9. Crear la estructura inicial

Dentro de `backend`:

```powershell
mkdir app
mkdir app\api
mkdir app\services
mkdir app\models
mkdir app\core
mkdir tests
mkdir models
```

La estructura:

```text
backend/
│
├── .venv/
│
├── app/
│   ├── __init__.py
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │
│   ├── services/
│   │   └── __init__.py
│   │
│   ├── models/
│   │   └── __init__.py
│   │
│   └── core/
│       └── __init__.py
│
├── models/
│
├── tests/
│
└── requirements.txt
```

----------

# 10. Crear nuestra primera API

Crea:

```text
app/main.py
```

Con:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Object Recognition API",
    description="API para reconocimiento de objetos mediante COCO",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "object-recognition-api",
    }
```

----------

# 11. Ejecutar FastAPI

Desde:

```text
backend/
```

con el entorno virtual activo:

```powershell
uvicorn app.main:app --reload
```

Deberías obtener:

```text
Uvicorn running on http://127.0.0.1:8000
```

Abre:

```text
http://127.0.0.1:8000/health
```

Deberías recibir:

```json
{
  "status": "ok",
  "service": "object-recognition-api"
}
```

----------

# 12. Documentación automática

Una de las grandes ventajas de FastAPI es que genera documentación automáticamente.

Abre:

```text
http://127.0.0.1:8000/docs
```

Ahí tendrás Swagger UI.

También:

```text
http://127.0.0.1:8000/redoc
```

Esto será particularmente útil para nuestro proyecto porque podremos probar:

```text
POST /recognize
POST /label
GET  /objects
GET  /detections
```

directamente desde el navegador.

----------

# 13. Crear el endpoint de reconocimiento

Ahora podemos preparar el endpoint que utilizará Next.js.

Crea:

```text
app/api/routes/recognition.py
```

Inicialmente:

```python
from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/recognition", tags=["Recognition"])


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
    }
```

Ahora modifica:

```text
app/main.py
```

a:

```python
from fastapi import FastAPI

from app.api.routes.recognition import router as recognition_router


app = FastAPI(
    title="Object Recognition API",
    description="API para reconocimiento de objetos mediante COCO",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "object-recognition-api",
    }


app.include_router(recognition_router)
```

Reinicia Uvicorn si fuera necesario.

En:

```text
http://127.0.0.1:8000/docs
```

ahora debería aparecer:

```text
Recognition

POST /recognition/predict
```

Y podrás subir una imagen.

----------

# 14. Instalar soporte para uploads

FastAPI necesita `python-multipart` para recibir archivos mediante `multipart/form-data`.

Instala:

```powershell
pip install python-multipart
```

Esto es importante porque nuestro frontend enviará:

```text
FormData
   │
   └── image: archivo
```

al backend.

----------

# 15. Instalar OpenCV

Aunque inicialmente podemos procesar las imágenes con Pillow, te recomiendo tener OpenCV disponible porque posteriormente puede ser útil para:

-   procesamiento de imágenes
    
-   vídeo
    
-   cámaras
    
-   conversión de frames
    
-   bounding boxes
    
-   preprocesamiento
    
-   visualización de detecciones
    

Instala:

```powershell
pip install opencv-python
```

Comprueba:

```powershell
python -c "import cv2; print(cv2.__version__)"
```

----------

# 16. Crear el servicio de reconocimiento

No metería TensorFlow directamente dentro del endpoint.

Es mejor:

```text
endpoint
   ↓
service
   ↓
model
```

Crea:

```text
app/services/recognition_service.py
```

Inicialmente:

```python
class RecognitionService:

    def __init__(self):
        self.model = None

    def load_model(self):
        pass

    def predict(self, image):
        pass
```

Más adelante tendremos:

```text
RecognitionService
│
├── load_model()
│
├── preprocess()
│
├── predict()
│
└── postprocess()
```

Esto nos permitirá cambiar el modelo sin tener que modificar toda la API.

----------

# 17. Preparar el modelo

La carpeta:

```text
models/
```

será para modelos locales si terminamos utilizando un modelo que necesite almacenarse en el proyecto.

Por ejemplo:

```text
models/
│
└── coco/
    └── ...
```

Pero **no descargues todavía un modelo arbitrario de COCO-SSD y lo metas ahí**.

Primero debemos decidir exactamente qué implementación utilizaremos.

----------

# 18. CORS para Next.js

Como tu frontend estará probablemente en:

```text
http://localhost:3000
```

y FastAPI en:

```text
http://localhost:8000
```

son dos orígenes diferentes.

Necesitamos CORS.

En:

```text
app/main.py
```

añade:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.recognition import router as recognition_router


app = FastAPI(
    title="Object Recognition API",
    description="API para reconocimiento de objetos mediante COCO",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "object-recognition-api",
    }


app.include_router(recognition_router)
```

Esto permitirá:

```text
Next.js :3000
     │
     │ HTTP
     ▼
FastAPI :8000
```

----------

# 19. Crear requirements.txt

Una vez instaladas las dependencias:

```powershell
pip freeze > requirements.txt
```

Tendrás algo parecido a:

```text
fastapi
uvicorn
tensorflow
numpy
pillow
opencv-python
python-multipart
...
```

No te preocupes si aparecen más dependencias indirectas.

----------

# 20. Probar que todo funciona

Haz:

```powershell
uvicorn app.main:app --reload
```

Después:

```text
http://localhost:8000/docs
```

Comprueba:

### Health

```text
GET /health
```

Resultado:

```json
{
  "status": "ok",
  "service": "object-recognition-api"
}
```

### Recognition

```text
POST /recognition/predict
```

Sube una imagen.

De momento:

```json
{
  "filename": "perro.jpg",
  "content_type": "image/jpeg"
}
```

Esto demuestra que tenemos funcionando:

```text
Next.js
   │
   │
   ▼
FastAPI
   │
   │
   ▼
Upload de imagen
```

El siguiente paso será:

```text
Upload
   ↓
Pillow/OpenCV
   ↓
TensorFlow
   ↓
COCO-SSD
   ↓
detecciones
   ↓
bounding boxes
   ↓
JSON
   ↓
Next.js
```

----------

## 21. Algo que cambiaría respecto a una instalación "rápida"

Para **tu proyecto concreto**, no recomiendo empezar instalando muchas librerías de machine learning al azar.

La base debería quedar:

```text
Python
 │
 ├── FastAPI
 ├── Uvicorn
 ├── TensorFlow
 ├── NumPy
 ├── Pillow
 ├── OpenCV
 └── python-multipart
```

y posteriormente:

```text
COCO-SSD
```

de forma compatible con el runtime elegido.

Esto es especialmente importante porque **COCO-SSD de TensorFlow.js y TensorFlow de Python no son exactamente la misma cosa**. Si tu requisito académico es específicamente **"COCO-SSD"**, podemos hacer que la arquitectura respete ese requisito, pero primero hay que decidir si:

1.  ejecutamos COCO-SSD mediante un runtime de TensorFlow.js desde el backend, o
    
2.  utilizamos una conversión/implementación compatible con TensorFlow Python.
    

Para un backend **100 % Python + FastAPI**, yo preferiría la segunda opción si encontramos una implementación fiable, porque mantiene una arquitectura limpia:

```text
Next.js
   ↓
FastAPI
   ↓
Python
   ↓
TensorFlow
   ↓
Modelo COCO
```

y deja al frontend completamente independiente del motor de IA.

**Con la base anterior ya tienes instalado el entorno backend y un endpoint funcional.** El siguiente paso lógico es montar el **motor de inferencia COCO-SSD**, incluyendo la carga del modelo una sola vez al arrancar FastAPI, procesamiento de imágenes y respuesta JSON con `class`, `confidence` y `boundingBox`, que es justamente el formato que necesitará el frontend que acabamos de preparar.
