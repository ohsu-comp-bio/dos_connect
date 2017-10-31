FROM python:2.7
COPY *.* /
RUN pip install -r requirements.txt
CMD BLOB_STORAGE_ACCOUNT=$BLOB_STORAGE_ACCOUNT \
  BLOB_STORAGE_ACCESS_KEY=$BLOB_STORAGE_ACCESS_KEY \
  python azure_inventory.py
