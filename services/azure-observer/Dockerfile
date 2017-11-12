FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD QUEUE_STORAGE_ACCOUNT=dostestingq \
  QUEUE_STORAGE_ACCESS_KEY=$QUEUE_STORAGE_ACCESS_KEY \
  BLOB_STORAGE_ACCOUNT=dostesting \
  BLOB_STORAGE_ACCESS_KEY=$BLOB_STORAGE_ACCESS_KEY \
  python python -m dos_connect.observers.azure_observer.py  --azure_queue $AZURE_QUEUE
