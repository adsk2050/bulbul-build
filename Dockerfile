# Bulbul Build on Render (free web service, Docker). render.yaml points here.
# Public site (PUBLIC_SITE=1): every demo but the pixel game. Render sets PORT.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv
# ffmpeg makes Talking Bulbul's share clips (/api/clip) and the phone-line audio.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 user && mkdir /app && chown user /app
WORKDIR /app
COPY --chown=user pyproject.toml uv.lock README.md ./
COPY --chown=user src ./src
USER user
RUN uv sync --frozen --no-dev
# The free disk is not kept between restarts, so the ledger and logs live in /tmp:
# the daily cap holds, the total cap counts from the last restart.
ENV HOST=0.0.0.0 \
    PUBLIC_SITE=1 \
    TRUST_PROXY=1 \
    LEDGER_PATH=/tmp/bulbul/ledger.sqlite \
    CACHE_DIR=/tmp/bulbul/cache
CMD ["/app/.venv/bin/bulbul-build"]
