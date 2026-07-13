FROM python:3.11-slim

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with UID 1000 for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Set environment defaults
ENV NIVESHMAP_API_URL=http://127.0.0.1:8000
ENV PYTHONPATH=.

# Copy the application source code and files
COPY --chown=user:user . .

# Install build backend and python dependencies from pyproject.toml in editable mode
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir -e .

# Make startup script executable
RUN chmod +x scripts/start.sh

# Expose Streamlit port
EXPOSE 7860

# Switch to non-root user
USER user

# Execute startup script
CMD ["/home/user/app/scripts/start.sh"]
