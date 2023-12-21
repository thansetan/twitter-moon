FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED True
WORKDIR /app
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]