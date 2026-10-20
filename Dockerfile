# MYA FaceSwap — FaceFusion (CUDA) + interfaz web simple en español
# Una sola imagen: el servicio "facefusion" corre la UI oficial (Gradio)
# y el servicio "mya-faceswap" corre la interfaz FastAPI que llama al CLI.
FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04

ARG FACEFUSION_VERSION=3.9.1
ENV GRADIO_SERVER_NAME=0.0.0.0 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    TZ=America/Monterrey \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /facefusion

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.12 python-is-python3 python3-pip git curl ffmpeg tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/facefusion/facefusion.git --branch ${FACEFUSION_VERSION} --single-branch . \
    && python install.py cuda@12 --skip-conda

# Interfaz simple MYA
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app/ /app/app/

EXPOSE 7860 8080
CMD ["python", "facefusion.py", "run", "--execution-providers", "cuda"]
