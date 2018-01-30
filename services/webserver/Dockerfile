FROM python:2.7
RUN apt-get install libssl-dev
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
RUN pip install -r /dos_connect/server/requirements.txt
CMD BACKEND=$BACKEND \
    ELASTIC_URL=$ELASTIC_URL \
    echo $ELASTIC_URL ; \
    python -m dos_connect.server.app --port $DOS_CONNECT_WEBSERVER_PORT
