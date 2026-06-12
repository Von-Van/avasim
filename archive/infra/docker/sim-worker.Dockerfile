FROM python:3.11-slim

WORKDIR /app

# Copy worker requirements
COPY apps/sim-worker/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker source
COPY apps/sim-worker/ ./

CMD ["python", "worker.py"]
