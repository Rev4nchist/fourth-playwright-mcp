FROM python:3.11-slim AS base

# Install system dependencies for Playwright browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Node dependencies first (better layer caching)
COPY package.json ./
RUN npm install

# Install Playwright browsers (chrome channel — @playwright/mcp looks for /opt/google/chrome/chrome)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN npx playwright install chrome --with-deps

# Install Python dependencies
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy application code
COPY src/ ./src/
COPY skills/ ./skills/

# Railway sets PORT automatically
ENV HOST=0.0.0.0
EXPOSE ${PORT:-8000}

CMD ["uv", "run", "python", "src/server.py"]
