FROM python:3.12-slim

WORKDIR /app
COPY app.py make_qr.py qrcodegen.py render.py sign.py config.json reports.json ./

ENV PYTHONUNBUFFERED=1
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8787/healthz',timeout=3)"

CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "8787"]
