ARG FUNCTION_DIR="/function"

FROM python:3.12 as build-image
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}
WORKDIR ${FUNCTION_DIR}
COPY ce ${FUNCTION_DIR}
RUN pip install -r requirements.txt -t ${FUNCTION_DIR}

FROM python:3.12-slim
ARG FUNCTION_DIR
ENV MPLCONFIGDIR=/tmp/matplotlib-cache
WORKDIR ${FUNCTION_DIR}
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
RUN ls
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "index.lambda_handler" ]