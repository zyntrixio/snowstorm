FROM ghcr.io/binkhq/python:3.12
ARG PIP_INDEX_URL
ARG APP_NAME
ARG APP_VERSION
RUN pip install --no-cache ${APP_NAME}==$(echo ${APP_VERSION} | cut -c 2-)
WORKDIR /app

ENTRYPOINT [ "/usr/local/bin/snowstorm" ]
