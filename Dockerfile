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

# 2. Copy ONLY the desired rule subdirectories from the build context to the temp location.
ARG INCLUDE_LINUX_RULES=false
ARG INCLUDE_NGINX_RULES=false
ARG INCLUDE_WINDOWS_RULES=false
COPY Sigma_Rules/ /context_sigma_rules/
RUN if [ "$INCLUDE_LINUX_RULES" = "true" ] ; then echo "Including Linux rules" && mv /context_sigma_rules/Linux /temp_sigma_rules/; fi
RUN if [ "$INCLUDE_NGINX_RULES" = "true" ] ; then echo "Including Nginx rules" && mv /context_sigma_rules/Nginx /temp_sigma_rules/; fi
RUN if [ "$INCLUDE_WINDOWS_RULES" = "true" ] ; then echo "Including Windows rules" && mv /context_sigma_rules/Windows /temp_sigma_rules/; fi
RUN rm -rf /context_sigma_rules

# 3. Copy the rest of your application's code. The main "Sigma_Rules" dir will be overwritten.
COPY . .

# 4. Move the selected rules from the temp location to the final destination.
RUN if [ -d "/temp_sigma_rules/Linux" ] || [ -d "/temp_sigma_rules/Nginx" ] || [ -d "/temp_sigma_rules/Windows" ]; then \
    rm -rf /app/Sigma_Rules && \
    mv /temp_sigma_rules /app/Sigma_Rules; \
    else \
    rm -rf /temp_sigma_rules && \
    mkdir -p /app/Sigma_Rules; \
    fi
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
