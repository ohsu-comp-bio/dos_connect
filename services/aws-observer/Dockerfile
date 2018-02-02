FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
    DOS_API_KEY=$DOS_API_KEY \
    python -m dos_connect.apps.observers.sqs_observer \
    --sqs_queue_name $SQS_QUEUE_NAME $OBSERVER_PARMS \
    --dos_server $DOS_SERVER
