# Use a more recent, stable version of the official Python runtime
FROM python:3.11-slim-bullseye

# Set environment variables with the key=value format
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies. Using a newer base image often has better repository support.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Add any system dependencies here, e.g., gcc, libpq-dev
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# We use a virtual environment to keep dependencies isolated
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Corrected Sigma Rules Logic ---
# 1. Create a temporary directory for the rules we want.
RUN mkdir -p /temp_sigma_rules


# --- Sigma Rules Args ---
ARG INCLUDE_LINUX=false
ARG INCLUDE_NGINX=false
ARG INCLUDE_WINDOWS=false
COPY Sigma_Rules/ /context_sigma_rules/
RUN if [ "$INCLUDE_LINUX" = "true" ] ; then echo "Including Linux rules" && mv /context_sigma_rules/Linux /temp_sigma_rules/; fi
RUN if [ "$INCLUDE_NGINX" = "true" ] ; then echo "Including Nginx rules" && mv /context_sigma_rules/Nginx /temp_sigma_rules/; fi
RUN if [ "$INCLUDE_WINDOWS" = "true" ] ; then echo "Including Windows rules" && mv /context_sigma_rules/Windows /temp_sigma_rules/; fi
RUN rm -rf /context_sigma_rules

# --- TTP Intelligence Args ---
RUN mkdir -p /temp_ttp_intel
ARG INCLUDE_TTP_LINUX=false
ARG INCLUDE_TTP_NGINX=false
ARG INCLUDE_TTP_WINDOWS=false
COPY TTP_Intelligence/ /context_ttp_intel/
RUN if [ "$INCLUDE_TTP_LINUX" = "true" ] ; then echo "Including TTP Linux" && mv /context_ttp_intel/Linux /temp_ttp_intel/; fi
RUN if [ "$INCLUDE_TTP_NGINX" = "true" ] ; then echo "Including TTP Nginx" && mv /context_ttp_intel/Nginx /temp_ttp_intel/; fi
RUN if [ "$INCLUDE_TTP_WINDOWS" = "true" ] ; then echo "Including TTP Windows" && mv /context_ttp_intel/Windows /temp_ttp_intel/; fi
RUN rm -rf /context_ttp_intel

# 3. Copy the rest of your application's code first.
COPY . .

# 4. Remove all Sigma/TTP rule folders, then move in only the selected ones.
RUN rm -rf /app/Sigma_Rules/Linux /app/Sigma_Rules/Nginx /app/Sigma_Rules/Windows
RUN if [ -d "/temp_sigma_rules/Linux" ]; then mv /temp_sigma_rules/Linux /app/Sigma_Rules/; fi
RUN if [ -d "/temp_sigma_rules/Nginx" ]; then mv /temp_sigma_rules/Nginx /app/Sigma_Rules/; fi
RUN if [ -d "/temp_sigma_rules/Windows" ]; then mv /temp_sigma_rules/Windows /app/Sigma_Rules/; fi
RUN rm -rf /temp_sigma_rules

RUN rm -rf /app/TTP_Intelligence/Linux /app/TTP_Intelligence/Nginx /app/TTP_Intelligence/Windows
RUN if [ -d "/temp_ttp_intel/Linux" ]; then mv /temp_ttp_intel/Linux /app/TTP_Intelligence/; fi
RUN if [ -d "/temp_ttp_intel/Nginx" ]; then mv /temp_ttp_intel/Nginx /app/TTP_Intelligence/; fi
RUN if [ -d "/temp_ttp_intel/Windows" ]; then mv /temp_ttp_intel/Windows /app/TTP_Intelligence/; fi
RUN rm -rf /temp_ttp_intel
# --- End of Corrected Logic ---

# Expose the ports your application needs
# TCP port for the web server
EXPOSE 8000
# UDP port for syslog
EXPOSE 5140/udp

# For data that needs to persist or be updated frequently (like your DB and Sigma rules),
# it is highly recommended to use Docker volumes.
# You can mount volumes when you run the container. For example:
# -v ./src/db:/app/src/db
# -v ./Sigma_Rules:/app/Sigma_Rules
# The run.sh script includes examples for this.

# Command to run your application
# We use uvicorn to run the FastAPI server.
# --host 0.0.0.0 makes it accessible from outside the container.
CMD ["uvicorn", "src.app.server:app", "--host", "0.0.0.0", "--port", "8000"]
