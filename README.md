# MYA FaceSwap — FaceFusion para ZimaOS (GPU NVIDIA)

Dos apps en una sola imagen:

| Servicio | Puerto | Qué es |
|---|---|---|
| `mya-faceswap` | **8095** | Interfaz simple en español: subes rostro(s) + foto/video → resultado. Cola de trabajos, historial, descarga. |
| `mya-facefusion` | **7870** | FaceFusion 3.9.1 oficial completo (Gradio): todos los procesadores (lip sync, edad, expresión, etc.). |

Resultados: `/DATA/Media/FaceSwap/` · Modelos: `/DATA/AppData/mya-faceswap/assets/` (se descargan solos la primera vez).

## Requisitos
- ZimaOS con GPU NVIDIA y drivers activos (`nvidia-smi` debe responder por SSH).
- ~15 GB libres (imagen CUDA + modelos).

## Instalación
1. Copia la carpeta `mya-faceswap` al servidor (por ejemplo a `/DATA/AppData/mya-faceswap-src/` vía la app Archivos de ZimaOS o con `scp`).
2. Por SSH:
   ```bash
   cd /DATA/AppData/mya-faceswap-src
   sh build.sh
   ```
   `build.sh` verifica la GPU, construye la imagen `mya/faceswap:3.9.1-cuda`, crea las carpetas e instala la app.
3. Alternativa por UI: tras construir la imagen, App Store → **+** → *Install a Custom App* → pega `docker-compose.yaml`.

## Uso
- Abre `http://zimaos.tanuki-chimaera.ts.net:8095`.
- El primer trabajo tarda más (descarga de modelos).
- Para video, desactiva "Mejora de rostro" si quieres más velocidad.

## Notas
- Usa solo rostros de personas que te dieron su consentimiento. El filtro de contenido de FaceFusion se mantiene activo.
- Para actualizar FaceFusion: cambia `FACEFUSION_VERSION` en el `Dockerfile` y el tag de imagen en `docker-compose.yaml` y `build.sh`.
