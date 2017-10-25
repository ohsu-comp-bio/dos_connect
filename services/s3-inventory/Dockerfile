FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD python s3_observer.py --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP 
