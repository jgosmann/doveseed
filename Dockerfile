FROM python:3.11-slim AS builder
ARG version

RUN python3 -m venv venv && \
    venv/bin/pip3 --disable-pip-version-check install doveseed==${version}

FROM python:3.11-alpine AS runner

RUN addgroup --system --gid 1000 doveseed &&\
    adduser --system --uid 1000 doveseed
USER doveseed

COPY --from=builder /venv /venv

EXPOSE 5000

ENV FLASK_APP="doveseed.app:create_app()"
ENTRYPOINT ["/venv/bin/python3", "-m", "flask", "run"]
