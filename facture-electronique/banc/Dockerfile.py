# Python image of the bench: factur-x (Akretion) and its dependencies, versions published before 30 June 2026
FROM python:3.12-slim
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends fonts-dejavu-core ghostscript >/dev/null && rm -rf /var/lib/apt/lists/*
RUN pip install -q uv && uv pip install -q --system --exclude-newer 2026-06-30 "factur-x==5.0" reportlab saxonche
WORKDIR /banc
