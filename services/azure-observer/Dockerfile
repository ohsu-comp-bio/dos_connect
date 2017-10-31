FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD QUEUE_STORAGE_ACCOUNT=dostestingq \
  QUEUE_STORAGE_ACCESS_KEY=Q85J1MXqLl2i3UlacF+xOih7AG7jAhHqeTX8bC+g+9PZkdWwoepKNTwhgcH7qgAs2scRMIwccE0lZxFG1QuLfQ== \
  BLOB_STORAGE_ACCOUNT=dostesting \
  BLOB_STORAGE_ACCESS_KEY=TAz4Ykz0EgIlLhhoEL/ur2OcSeythWxKYYyinkSArAxRcWakGbw7lBr5JsfUKvNHHhF1OKNlYYpP+XVR/Btl/A== \
  python azure_observer.py  -d

CMD  GOOGLE_APPLICATION_CREDENTIALS=/google-auth.json  python pubsub_observer.py  --kafka_topic $KAFKA_TOPIC --kafka_bootstrap $KAFKA_BOOTSTRAP
