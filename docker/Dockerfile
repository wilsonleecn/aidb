FROM python:3.9-slim

# Install the latest OpenAI library (>=0.27.0)
RUN pip install --upgrade pip && \
    pip install pymysql configparser && \
    pip install --no-cache-dir --upgrade openai

CMD ["python3"]

