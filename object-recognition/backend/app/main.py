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