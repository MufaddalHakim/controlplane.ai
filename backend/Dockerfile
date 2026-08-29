FROM python:3.12-slim
WORKDIR /workspace
COPY backend/requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir -r /workspace/backend/requirements.txt
COPY backend/app /workspace/backend/app
COPY config /workspace/config
COPY data /workspace/data
WORKDIR /workspace/backend
RUN mkdir -p /workspace/state
ENV DEMO_MODE=true DATABASE_URL=sqlite:////workspace/state/controlplane.db AUDIT_STORE_RAW=false
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
