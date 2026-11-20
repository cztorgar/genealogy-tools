# Dashboard workbenche v kontejneru. Kód ani data se do obrazu nekopírují — workbench a stromy se připojí
# jako svazky (infra/gramps-web/docker-compose.yml, služba `dashboard`), server čte živé soubory.
FROM python:3.12-slim
RUN pip install --no-cache-dir "pyyaml>=6"
WORKDIR /ws/genealogy-tools
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 5056
CMD ["python", "tools/dashboard/server.py", "--host", "0.0.0.0", "--port", "5056", "--gramps-url", "http://localhost:5055"]
