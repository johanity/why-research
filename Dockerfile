FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY SKILL.md .
COPY AGENTS.md .
COPY .well-known/ .well-known/

RUN pip install --no-cache-dir .

ENV WHY_MODEL=claude-sonnet-4-20250514

EXPOSE 8420

ENTRYPOINT ["why"]
