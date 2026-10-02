# Packages the data analysis script and its dependencies into a Docker image.
FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENV MPLBACKEND=Agg
CMD ["python", "data_analysis.py"]