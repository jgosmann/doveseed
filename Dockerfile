FROM python:3.13-slim AS builder
ARG version

RUN python3 -m venv venv && \
    venv/bin/pip3 --disable-pip-version-check install gunicorn==23.0.0 uvicorn==0.32.0 'doveseed[all]'==${version}

FROM python:3.13-alpine AS runner

ENV DOVESEED_APP=doveseed.app:app

RUN apk add curl

RUN addgroup --system --gid 1000 doveseed &&\
    adduser --system --uid 1000 doveseed
USER doveseed

COPY --from=builder /venv /venv

HEALTHCHECK --start-period=5s CMD ["curl", "--fail", "http://localhost:5000/health"]

EXPOSE 5000

ENV FLASK_APP="doveseed.app:create_app()"
ENTRYPOINT ["/venv/bin/python3", "-m", "gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:5000"]
CMD ["doveseed.app:app"]
