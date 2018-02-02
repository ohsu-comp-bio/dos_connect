FROM python:2.7
RUN apt-get install libssl-dev
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
RUN pip install -r /dos_connect/server/requirements.txt
CMD \
  OS_AUTH_URL=$OS_AUTH_URL \
  AUTHORIZER=$AUTHORIZER \
  BACKEND=$BACKEND \
  ELASTIC_URL=$ELASTIC_URL \
  KAFKA_DOS_TOPIC=$KAFKA_DOS_TOPIC \
  KAFKA_BOOTSTRAP_SERVERS=$KAFKA_BOOTSTRAP_SERVERS \
  python -m dos_connect.server.app --port $DOS_CONNECT_WEBSERVER_PORT
