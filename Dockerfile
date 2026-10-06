FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    ENV_FINDER_ROOT=/scan ENV_FINDER_DEFAULT=/scan
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py settings.py .
COPY templates templates
COPY static static
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "5000"]
