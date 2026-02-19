FROM python:3.13-slim

# Install system dependencies for postgres (psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app

# Install the libraries needed for your notebook
RUN pip install pandas sqlalchemy psycopg2 pyarrow jupyter

# We will mount your local files, so no need to COPY them here for dev
EXPOSE 8888

ENTRYPOINT ["jupyter", "notebook", "--ip=0.0.0.0", "--allow-root", "--no-browser"]