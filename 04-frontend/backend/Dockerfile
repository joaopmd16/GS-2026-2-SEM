FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd -m citizen && mkdir -p /data/runtime && chown -R citizen /data
USER citizen
ENV RUNTIME_CSV=/data/runtime/ocorrencias.csv OCORRENCIAS_CSV=/data/ocorrencias.csv
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
