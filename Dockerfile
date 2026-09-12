FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . .

CMD ["python", "main.py"]