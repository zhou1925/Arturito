FROM python:3.10-slim-bullseye

# --- Environment Variables ---
ENV TZ=America/Lima
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Working Directory ---
WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# --- Command ---

CMD ["python", "main.py"]