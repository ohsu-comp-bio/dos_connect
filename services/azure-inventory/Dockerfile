FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD BLOB_STORAGE_ACCOUNT=$BLOB_STORAGE_ACCOUNT \
  BLOB_STORAGE_ACCESS_KEY=$BLOB_STORAGE_ACCESS_KEY \
  python python -m dos_connect.inventory.azure_inventory.py --azure_container $AZURE_CONTAINER
