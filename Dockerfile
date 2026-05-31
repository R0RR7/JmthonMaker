FROM python:3.10-slim-buster

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y ffmpeg mediainfo p7zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app/

CMD ["python3","-m","jmthon"]
