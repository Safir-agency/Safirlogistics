FROM python:3.11.2-slim-buster
WORKDIR .
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]