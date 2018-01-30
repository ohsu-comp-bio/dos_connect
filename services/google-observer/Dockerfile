FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD  GOOGLE_APPLICATION_CREDENTIALS=/google-auth.json  \
python -m dos_connect.apps.observers.pubsub_observer  \
--google_cloud_project $GOOGLE_CLOUD_PROJECT \
--google_topic $GOOGLE_TOPIC \
--dos_server $DOS_SERVER \
--google_subscription_name $GOOGLE_SUBSCRIPTION_NAME
