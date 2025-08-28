FROM node:lts-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies including build tools for Python packages
RUN apt-get update && apt-get install -y \
    git \
    xvfb \
    x11vnc \
    openbox \
    supervisor \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    novnc \
    websockify \
    procps \
    xdg-utils \
    python3-xdg \
    x11-xserver-utils \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install noVNC
RUN git clone --depth 1 --branch v1.6.0 https://github.com/novnc/noVNC.git /usr/local/novnc \
    && git clone --depth 1 --branch v0.13.0 https://github.com/novnc/websockify /usr/local/novnc/utils/websockify

# Set up working directory
WORKDIR /app

# Install Playwright
COPY package.json package-lock.json* ./
RUN npm install .

# Install browsers with dependencies
RUN npx playwright@1.51 install --with-deps chromium

# Create Python virtual environment and install browser-use
RUN python3 -m venv /opt/browser-use-venv
ENV PATH="/opt/browser-use-venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir \
    browser-use \
    flask \
    flask-cors \
    nest-asyncio \
    playwright \
    openai \
    pydantic \
    python-dotenv \
    requests \
    aiohttp

# Install Playwright for Python and browsers
RUN playwright install chromium

# Set up supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy scripts and ProcessGPT server files
COPY start.sh /app/start.sh
COPY playwright-server.js /app/playwright-server.js
COPY x11-setup.sh /app/x11-setup.sh
COPY browser-use-server.py /app/browser-use-server.py
COPY processgpt_browser_server.py /app/processgpt_browser_server.py
COPY processgpt_browser_server_standalone.py /app/processgpt_browser_server_standalone.py
COPY processgpt_browser_server_supabase.py /app/processgpt_browser_server_supabase.py
COPY browser_use_agent_executor.py /app/browser_use_agent_executor.py
COPY test_processgpt_integration.py /app/test_processgpt_integration.py
COPY integrated_browser_server.py /app/integrated_browser_server.py
COPY run_integrated_server.py /app/run_integrated_server.py
COPY test_integrated_server.py /app/test_integrated_server.py
COPY browser_use_agent.py /app/browser_use_agent.py

# Make scripts executable
RUN chmod +x /app/start.sh /app/x11-setup.sh /app/run_integrated_server.py /app/processgpt_browser_server.py

# Create a simple openbox configuration to only show the browser window
RUN mkdir -p /root/.config/openbox
COPY openbox-rc.xml /root/.config/openbox/rc.xml

# Expose ports: noVNC web interface, Playwright server, and Browser-Use API
EXPOSE 6080 37367 5001

ENV PLAYWRIGHT_WS_PATH="default"

# Set the display environment variable
ENV DISPLAY=:99

RUN mkdir -p /workspace
WORKDIR /workspace

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

LABEL org.opencontainers.image.source=https://github.com/microsoft/magentic-ui
LABEL org.opencontainers.image.description="Magentic UI Browser Docker container with Playwright and noVNC"
LABEL org.opencontainers.image.licenses=MIT

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Start services
CMD ["/app/start.sh"]