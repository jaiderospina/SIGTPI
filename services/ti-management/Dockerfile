FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install service dependencies (no sigtpi_common here — loaded via PYTHONPATH)
COPY services/ti-management/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy shared library and service source
COPY shared/sigtpi_common /app/shared/sigtpi_common
COPY services/ti-management/app /app/app

# PYTHONPATH includes both /app (for app.*) and the shared library root
ENV PYTHONPATH=/app:/app/shared/sigtpi_common
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]
