FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD  GOOGLE_APPLICATION_CREDENTIALS=/google-auth.json  python gs_inventory.py  --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP 

