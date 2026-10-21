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

## Instalación (un solo comando)
Entra por SSH a ZimaOS (`ssh Alan@zimaos.tanuki-chimaera.ts.net`) y pega:
```bash
curl -fsSL https://raw.githubusercontent.com/Vladalan/mya-faceswap/main/install.sh | sudo sh
```
Revisa la GPU, descarga el proyecto, obtiene o construye la imagen (10–20 min), crea las carpetas e instala la app. Para actualizar, corre el mismo comando otra vez.

Instructivo completo: [`instalacion/INSTALACION_mya-faceswap.pdf`](instalacion/INSTALACION_mya-faceswap.pdf).

## Uso
- Abre `http://zimaos.tanuki-chimaera.ts.net:8095`.
- El primer trabajo tarda más (descarga de modelos).
- Para video, desactiva "Mejora de rostro" si quieres más velocidad.

## Notas
- Usa solo rostros de personas que te dieron su consentimiento. El filtro de contenido de FaceFusion se mantiene activo.
- Para actualizar FaceFusion: cambia `FACEFUSION_VERSION` en el `Dockerfile` y el tag de imagen en `docker-compose.yaml` y `build.sh`.
