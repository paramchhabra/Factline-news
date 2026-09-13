FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv pip install --system -r requirements.txt

CMD ["python", "main.py"]