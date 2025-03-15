FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Set default environment variables
ENV PORT=3000 \
    TRANSPORT_TYPE=sse \
    fetch_html=Disable

# Expose port
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["sh", "-c", "if [ \"$TRANSPORT_TYPE\" = \"sse\" ]; then playwright-mcp-fetch-sse; else playwright-mcp-fetch; fi"] 