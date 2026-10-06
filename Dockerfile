# Stage 1: Install dependencies in a virtual environment
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && \ 
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Creating runtime image with only what is needed from the builder stage
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1
COPY data_analysis.py All_Diets.csv ./
CMD ["python", "data_analysis.py"]