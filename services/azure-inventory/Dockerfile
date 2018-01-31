FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD BLOB_STORAGE_ACCOUNT=$BLOB_STORAGE_ACCOUNT \
  BLOB_STORAGE_ACCESS_KEY=$BLOB_STORAGE_ACCESS_KEY \
  DOS_API_KEY=$DOS_API_KEY \
  python -m dos_connect.apps.inventory.azure_inventory \
  --azure_container $BUCKET_NAME \
  --dos_server $DOS_SERVER
