FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD python -m dos_connect.sinks.elastic_sink \
    --kafka_topic $KAFKA_TOPIC \
    --kafka_bootstrap $KAFKA_BOOTSTRAP \
    --elastic $ELASTIC_URL \
    --enable_auto_commit
