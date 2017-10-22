FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD python server.py -P $OBSERVER_PORT -H 0.0.0.0  --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP

