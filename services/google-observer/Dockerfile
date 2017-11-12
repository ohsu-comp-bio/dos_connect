FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD  GOOGLE_APPLICATION_CREDENTIALS=/google-auth.json  \
python -m dos_connect.observers.pubsub_observer  --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP 
