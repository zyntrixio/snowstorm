FROM ghcr.io/binkhq/python:3.11-poetry as build
WORKDIR /src
ADD . .
RUN poetry build

FROM ghcr.io/binkhq/python:3.11
WORKDIR /app
COPY --from=build /src/dist/*.whl .
RUN pip install *.whl && rm *.whl
COPY --from=build /src/alembic/ ./alembic/
COPY --from=build /src/alembic.ini .

ENTRYPOINT [ "linkerd-await", "--" ]
CMD [ "/usr/local/bin/stormctl" ]
