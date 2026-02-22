FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set PYTHONPATH so python can resolve the src package
ENV PYTHONPATH=/app

# Command to run bot
CMD ["python", "-m", "src.main"]
