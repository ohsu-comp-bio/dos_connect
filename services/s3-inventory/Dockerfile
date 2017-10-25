FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD python file_observer.py --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP
CMD AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
    python s3_inventory.py --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP --sqs_queue_name $SQS_QUEUE_NAME
