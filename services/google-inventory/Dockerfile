FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD  GOOGLE_APPLICATION_CREDENTIALS=/google-auth.json \
    DOS_API_KEY=$DOS_API_KEY \
python -m dos_connect.apps.inventory.gs_inventory  \
--dos_server $DOS_SERVER \
$BUCKET_NAME
