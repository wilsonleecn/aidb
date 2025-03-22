FROM python:3.9-slim

# Install the latest OpenAI library (>=0.27.0)
RUN pip install --upgrade pip && \
    pip install pymysql configparser flask==3.0.2 && \
    pip install --no-cache-dir --upgrade openai

CMD ["python3"]

