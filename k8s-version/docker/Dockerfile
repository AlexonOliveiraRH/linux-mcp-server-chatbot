# Linux MCP Server Chatbot - Multi-architecture container image
# Supports: amd64, arm64
# Base: Python 3.11 with SSH client for remote host access

FROM python:3.11-slim

LABEL maintainer="Your Organization"
LABEL description="AI-powered Linux diagnostics chatbot with MCP integration"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root for security)
RUN useradd -m -u 1001 -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Linux MCP Server
RUN pip install --no-cache-dir linux-mcp-server

# Copy application code
COPY app.py .
COPY mcp_client.py .
COPY claude_vertex_wrapper.py .

# Create directories for configuration and SSH
RUN mkdir -p /app/config /home/appuser/.ssh /home/appuser/.ssh/controlmasters && \
    chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Environment variables (can be overridden)
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
    MCP_COMMAND=/usr/local/bin/linux-mcp-server

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
