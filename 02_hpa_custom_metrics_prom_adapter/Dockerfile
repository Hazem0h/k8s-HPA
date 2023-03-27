FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt requirements.txt
EXPOSE 9000 
EXPOSE 8000
RUN pip install -r requirements.txt
COPY app.py app.py
CMD ["python", "app.py"]