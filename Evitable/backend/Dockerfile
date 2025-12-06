FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
# We just need to install the packages. Since we used uv/pip individually, let's just reinstall via pip
# leveraging cache.
RUN pip install duckdb polars pyarrow python-dotenv requests tenacity great-tables sqlglot beautifulsoup4 tqdm ipykernel scipy numpy pandas rich fastapi uvicorn

COPY . .

EXPOSE 8000
