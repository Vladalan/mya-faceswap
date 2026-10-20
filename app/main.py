"""MYA FaceSwap — interfaz simple sobre el CLI de FaceFusion.

Cola de trabajos en un solo hilo (la GPU procesa uno a la vez).
Los trabajos se guardan en SQLite; entradas y resultados en /data.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path
from queue import Queue

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

FACEFUSION_DIR = Path(os.getenv("FACEFUSION_DIR", "/facefusion"))
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/output"))
EXECUTION_PROVIDER = os.getenv("EXECUTION_PROVIDER", "cuda")
DB_PATH = DATA_DIR / "jobs.db"
INPUT_DIR = DATA_DIR / "inputs"
TEMP_DIR = DATA_DIR / "tmp"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
SWAPPER_MODELS = {
    "hyperswap_1a_256", "hyperswap_1b_256", "hyperswap_1c_256", "inswapper_128_fp16", "inswapper_128",
    "simswap_256", "simswap_unofficial_512", "ghost_2_256", "blendswap_256", "uniface_256",
}
ENHANCER_MODELS = {"gfpgan_1.4", "codeformer", "restoreformer_plus_plus", "gpen_bfr_512"}

for d in (INPUT_DIR, TEMP_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MYA FaceSwap")
cola: Queue = Queue()
db_lock = threading.Lock()


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


with db() as con:
    con.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, creado REAL, estado TEXT, objetivo TEXT,
            salida TEXT, opciones TEXT, log TEXT, terminado REAL)"""
    )
    # Trabajos interrumpidos por un reinicio vuelven a la cola
    pendientes = [r["id"] for r in con.execute("SELECT id FROM jobs WHERE estado IN ('en_cola','procesando')")]
    con.execute("UPDATE jobs SET estado='en_cola' WHERE estado='procesando'")


def actualizar(job_id: str, **campos):
    with db_lock, db() as con:
        sets = ", ".join(f"{k}=?" for k in campos)
        con.execute(f"UPDATE jobs SET {sets} WHERE id=?", (*campos.values(), job_id))


def construir_comando(job_dir: Path, salida: Path, opciones: dict) -> list[str]:
    fuentes = sorted(str(p) for p in job_dir.glob("source_*"))
    objetivo = next(job_dir.glob("target*"))
    procesadores = ["face_swapper"]
    if opciones["mejorar"]:
        procesadores.append("face_enhancer")
    cmd = [
        "python", "facefusion.py", "headless-run",
        "--source-paths", *fuentes,
        "--target-path", str(objetivo),
        "--output-path", str(salida),
        "--processors", *procesadores,
        "--execution-providers", EXECUTION_PROVIDER,
        "--temp-path", str(TEMP_DIR),
        "--face-swapper-model", opciones["modelo"],
        "--face-selector-mode", "many" if opciones["todas_caras"] else "reference",
        "--output-video-quality", str(opciones["calidad"]),
    ]
    if opciones["mejorar"]:
        cmd += ["--face-enhancer-model", opciones["modelo_mejora"]]
    return cmd


def trabajador():
    while True:
        job_id = cola.get()
        with db() as con:
            row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row or row["estado"] != "en_cola":
            continue
        opciones = json.loads(row["opciones"])
        salida = OUTPUT_DIR / row["salida"]
        actualizar(job_id, estado="procesando")
        try:
            proc = subprocess.run(
                construir_comando(INPUT_DIR / job_id, salida, opciones),
                cwd=FACEFUSION_DIR, capture_output=True, text=True, timeout=6 * 3600,
            )
            log = (proc.stdout + proc.stderr)[-8000:]
            ok = proc.returncode == 0 and salida.exists()
            actualizar(job_id, estado="listo" if ok else "error", log=log, terminado=time.time())
        except Exception as e:  # noqa: BLE001
            actualizar(job_id, estado="error", log=str(e), terminado=time.time())


threading.Thread(target=trabajador, daemon=True).start()
for _id in pendientes:
    cola.put(_id)


def guardar(upload: UploadFile, destino: Path):
    with destino.open("wb") as f:
        shutil.copyfileobj(upload.file, f)


@app.post("/api/swap")
async def crear_trabajo(
    rostros: list[UploadFile] = File(...),
    objetivo: UploadFile = File(...),
    modelo: str = Form("hyperswap_1a_256"),
    mejorar: bool = Form(True),
    modelo_mejora: str = Form("gfpgan_1.4"),
    todas_caras: bool = Form(False),
    calidad: int = Form(90),
    consentimiento: bool = Form(False),
):
    if not consentimiento:
        raise HTTPException(400, "Debes confirmar que tienes consentimiento de las personas involucradas.")
    if modelo not in SWAPPER_MODELS or modelo_mejora not in ENHANCER_MODELS:
        raise HTTPException(400, "Modelo no válido.")
    ext_obj = Path(objetivo.filename or "").suffix.lower()
    if ext_obj not in IMAGE_EXT | VIDEO_EXT:
        raise HTTPException(400, "El objetivo debe ser imagen o video.")
    for r in rostros:
        if Path(r.filename or "").suffix.lower() not in IMAGE_EXT:
            raise HTTPException(400, "Los rostros fuente deben ser imágenes.")

    job_id = uuid.uuid4().hex[:12]
    job_dir = INPUT_DIR / job_id
    job_dir.mkdir(parents=True)
    for i, r in enumerate(rostros):
        guardar(r, job_dir / f"source_{i}{Path(r.filename).suffix.lower()}")
    guardar(objetivo, job_dir / f"target{ext_obj}")

    opciones = {
        "modelo": modelo, "mejorar": mejorar, "modelo_mejora": modelo_mejora,
        "todas_caras": todas_caras, "calidad": max(10, min(100, calidad)),
    }
    salida = f"faceswap_{time.strftime('%Y%m%d_%H%M%S')}_{job_id}{ext_obj}"
    with db_lock, db() as con:
        con.execute(
            "INSERT INTO jobs (id, creado, estado, objetivo, salida, opciones) VALUES (?,?,?,?,?,?)",
            (job_id, time.time(), "en_cola", objetivo.filename, salida, json.dumps(opciones)),
        )
    cola.put(job_id)
    return {"id": job_id}


@app.get("/api/jobs")
def listar():
    with db() as con:
        rows = con.execute(
            "SELECT id, creado, estado, objetivo, salida, terminado FROM jobs ORDER BY creado DESC LIMIT 100"
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/jobs/{job_id}")
def detalle(job_id: str):
    with db() as con:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, "No existe.")
    return dict(row)


@app.get("/api/jobs/{job_id}/resultado")
def resultado(job_id: str, descargar: bool = False):
    job = detalle(job_id)
    ruta = OUTPUT_DIR / job["salida"]
    if job["estado"] != "listo" or not ruta.exists():
        raise HTTPException(404, "Resultado no disponible.")
    return FileResponse(ruta, filename=job["salida"] if descargar else None)


@app.delete("/api/jobs/{job_id}")
def borrar(job_id: str):
    job = detalle(job_id)
    if job["estado"] == "procesando":
        raise HTTPException(409, "No se puede borrar mientras se procesa.")
    shutil.rmtree(INPUT_DIR / job_id, ignore_errors=True)
    (OUTPUT_DIR / job["salida"]).unlink(missing_ok=True)
    with db_lock, db() as con:
        con.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    return {"ok": True}


@app.get("/api/estado")
def estado():
    gpu = "no detectada"
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            gpu = r.stdout.strip()
    except FileNotFoundError:
        pass
    return {"gpu": gpu, "en_cola": cola.qsize(), "proveedor": EXECUTION_PROVIDER}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
