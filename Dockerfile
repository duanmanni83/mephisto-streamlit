# Mephisto Streamlit App with CIGALE
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install CIGALE
RUN cd /opt && \
    git clone --depth 1 https://gitlab.lam.fr/cigale/cigale.git cigale-v2025.0 && \
    cd cigale-v2025.0 && \
    python setup.py build && \
    pip install -e .

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "mephisto_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
