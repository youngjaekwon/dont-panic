FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
WORKDIR /srv
COPY services/coupon/pyproject.toml services/coupon/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY gen/python ./gen
COPY services/coupon/alembic.ini ./
COPY services/coupon/migrations ./migrations
COPY services/coupon/app ./app
ENV PATH="/srv/.venv/bin:$PATH" PYTHONPATH=/srv/gen
CMD ["python", "-m", "app.main"]
