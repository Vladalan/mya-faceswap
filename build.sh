#!/bin/sh
# Ejecutar en ZimaOS (por SSH) dentro de la carpeta del proyecto.
set -e
cd "$(dirname "$0")"

echo "== Verificando GPU NVIDIA =="
nvidia-smi || { echo "ERROR: nvidia-smi no responde. Activa los drivers NVIDIA en ZimaOS (Ajustes > GPU)."; exit 1; }

echo "== Construyendo imagen (tarda 10-20 min la primera vez) =="
docker build -t mya/faceswap:3.9.1-cuda .

mkdir -p /DATA/AppData/mya-faceswap/assets /DATA/AppData/mya-faceswap/caches \
         /DATA/AppData/mya-faceswap/jobs /DATA/AppData/mya-faceswap/data /DATA/Media/FaceSwap

echo "== Instalando app en ZimaOS =="
if command -v casaos-cli >/dev/null 2>&1; then
  casaos-cli app-management install --file docker-compose.yaml \
    || casaos-cli app-management compose install --file docker-compose.yaml
else
  docker compose -f docker-compose.yaml up -d
fi

echo "== Listo =="
echo "Interfaz simple:      http://zimaos.tanuki-chimaera.ts.net:8095"
echo "FaceFusion avanzado:  http://zimaos.tanuki-chimaera.ts.net:7870"
