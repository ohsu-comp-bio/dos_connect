FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD QUEUE_STORAGE_ACCOUNT=dostestingq \
  QUEUE_STORAGE_ACCESS_KEY=$QUEUE_STORAGE_ACCESS_KEY \
  BLOB_STORAGE_ACCOUNT=dostesting \
  BLOB_STORAGE_ACCESS_KEY=$BLOB_STORAGE_ACCESS_KEY \
  python -m dos_connect.apps.observers.azure_observer  --azure_queue $AZURE_QUEUE \
  --dos_server $DOS_SERVER
