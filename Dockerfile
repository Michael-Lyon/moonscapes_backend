# Use an x86 base image because Aspose for Python via .NET does not support ARM
FROM --platform=linux/amd64 mcr.microsoft.com/dotnet/runtime:7.0-bullseye-slim AS base

# Install required dependencies
RUN apt-get update \
    && apt-get install -y \
    libc6-dev \
    libicu-dev \
    libssl-dev \
    libcurl4 \
    libunwind8 \
    zlib1g \
    curl \
    build-essential \
    git \
    python3-dev \
    python3-pip \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the latest .NET SDK
RUN curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --channel 7.0 \
    && ln -s /root/.dotnet/dotnet /usr/local/bin/

# Set environment variables for Aspose
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV PATH="/root/.dotnet:${PATH}"

# Create working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

EXPOSE 8000
# Run the Django application
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]