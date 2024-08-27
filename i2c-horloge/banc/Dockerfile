FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends sigrok-cli python3 poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /banc
