FROM chenlb/python:3.11.11

ARG APP_HOME=/home/admin/langfarm-tracing

WORKDIR $APP_HOME

RUN chown admin:admin -R $APP_HOME

COPY --chown=admin:admin langfarm_tracing $APP_HOME/langfarm_tracing
COPY --chown=admin:admin main.py $APP_HOME
COPY --chown=admin:admin ping_db.py $APP_HOME
COPY --chown=admin:admin pyproject.toml $APP_HOME
COPY --chown=admin:admin poetry.lock $APP_HOME
COPY --chown=admin:admin logging.yaml $APP_HOME
COPY --chown=admin:admin docker/entrypoint.sh $APP_HOME
COPY --chown=admin:admin docker/.env $APP_HOME

RUN chmod +x ./entrypoint.sh

USER admin

ARG PYTHON_HOME=/home/admin/.local
RUN ${PYTHON_HOME}/bin/poetry install --without=dev

ENV PORT=3080

ENTRYPOINT ["dumb-init"]

# startup command
CMD ["sh", "./entrypoint.sh"]
