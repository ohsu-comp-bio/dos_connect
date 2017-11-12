FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD python -m dos_connect.observers.file_observer --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP $OBSERVER_PARMS $MONITOR_DIRECTORY
