FROM python:3.11-slim
WORKDIR /app
COPY extract.py transform.py load.py ./
RUN pip install --no-cache-dir requests pandas sqlalchemy psycopg2-binary

CMD ["python", "load.py"]