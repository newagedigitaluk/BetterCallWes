# Better Call Wes booking-api
# Runs FastAPI on uvicorn behind Coolify's reverse proxy.
#
# Build context: this Dockerfile expects to be built from the PARENT
# `website/` directory so it can pick up services.json from site/data/.
# Coolify config:
#   Base Directory:  website/
#   Dockerfile path: booking-api/Dockerfile
#
# Local dev build:
#   cd website && docker build -f booking-api/Dockerfile -t bcw-booking-api .

FROM python:3.12-slim AS base

RUN groupadd --gid 1000 app && \
    useradd  --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

# Install deps first (cached when requirements unchanged)
COPY booking-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY booking-api/*.py ./

# Services config (single source of truth for both website + API)
COPY site/data/services.json /app/services.json
ENV SERVICES_JSON=/app/services.json

USER app

EXPOSE 8000
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        r = urllib.request.urlopen('http://127.0.0.1:8000/api/healthcheck', timeout=4); \
        sys.exit(0 if r.status == 200 else 1)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
