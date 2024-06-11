# Start from the Debian Bookworm base image
FROM debian:bookworm

# Update the package lists and install Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3.11-venv && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install packages inside the virtual environment
RUN pip install --upgrade pip