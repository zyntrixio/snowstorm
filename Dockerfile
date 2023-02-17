FROM ghcr.io/binkhq/python:3.11-poetry as build
WORKDIR /src
ADD . .
RUN poetry build

FROM docker.io/node:latest as frontend
WORKDIR /build
ADD lbg-stats-frontend/ .
RUN npm install && npm run build

FROM ghcr.io/binkhq/python:3.11
WORKDIR /app
COPY --from=frontend /build/dist/ /app/frontend
COPY --from=build /src/dist/*.whl .
RUN pip install *.whl && rm *.whl
COPY --from=build /src/alembic/ ./alembic/
COPY --from=build /src/alembic.ini .

ENTRYPOINT [ "linkerd-await", "--" ]
CMD [ "/usr/local/bin/stormctl" ]
