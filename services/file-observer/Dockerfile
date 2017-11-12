FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD python -m dos_connect.observers.file_observer.py --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP $OBSERVER_PARMS $MONITOR_DIRECTORY
