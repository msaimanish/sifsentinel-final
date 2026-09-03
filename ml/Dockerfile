FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/workspace:/workspace/backend

RUN apt-get update && \
    apt-get install -y build-essential git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /workspace/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch && \
    pip install --no-cache-dir \
        -r /workspace/requirements.txt

COPY pipeline /workspace/pipeline
COPY models /workspace/models

CMD ["python", "-m", "pipeline.worker"]