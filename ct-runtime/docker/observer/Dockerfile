FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests pyyaml

COPY agent.py /app/agent.py
COPY agent.yaml /app/agent.yaml

ENV PYTHONUNBUFFERED=1 \
    AGENT_YAML_PATH=/app/agent.yaml \
    HEALTH_PORT=8080

EXPOSE 8080

USER 1000:1000

CMD ["python", "/app/agent.py"]
