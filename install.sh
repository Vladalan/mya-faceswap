#!/bin/sh
# Instalador de MYA FaceSwap para ZimaOS — un solo comando:
#   curl -fsSL https://raw.githubusercontent.com/Vladalan/mya-faceswap/main/install.sh | sudo sh
set -e

REPO="https://github.com/Vladalan/mya-faceswap/archive/refs/heads/main.tar.gz"
IMAGEN="ghcr.io/vladalan/mya-faceswap:3.9.1-cuda"
SRC="/DATA/AppData/mya-faceswap/src"
HOST="$(hostname)"

paso() { printf '\n\033[1;34m== %s ==\033[0m\n' "$1"; }
error() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$1"; exit 1; }

paso "1/5 Revisando GPU NVIDIA"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader \
  || error "No se detecta la GPU. Activa los drivers NVIDIA en ZimaOS (Ajustes > GPU) y vuelve a correr este comando."

paso "2/5 Descargando el proyecto"
rm -rf "$SRC" && mkdir -p "$SRC"
curl -fsSL "$REPO" | tar -xz -C "$SRC" --strip-components=1
cd "$SRC"

paso "3/5 Obteniendo la imagen (puede tardar 10-20 min)"
if docker pull "$IMAGEN" 2>/dev/null; then
  echo "Imagen descargada de GitHub."
else
  echo "No se pudo descargar; se construye aquí mismo..."
  docker build -t "$IMAGEN" .
fi

paso "4/5 Creando carpetas"
mkdir -p /DATA/AppData/mya-faceswap/assets /DATA/AppData/mya-faceswap/caches \
         /DATA/AppData/mya-faceswap/jobs /DATA/AppData/mya-faceswap/data /DATA/Media/FaceSwap

paso "5/5 Instalando la app"
if command -v casaos-cli >/dev/null 2>&1 && \
   { casaos-cli app-management install --file docker-compose.yaml 2>/dev/null \
     || casaos-cli app-management compose install --file docker-compose.yaml 2>/dev/null; }; then
  echo "App registrada en el panel de ZimaOS."
else
  docker compose -f docker-compose.yaml up -d
  echo "App iniciada con Docker Compose."
fi

printf '\n\033[1;32m✔ Listo.\033[0m\n'
echo "  Interfaz simple:     http://$HOST:8095"
echo "  FaceFusion avanzado: http://$HOST:7870"
echo "  (por Tailscale: http://zimaos.tanuki-chimaera.ts.net:8095)"
