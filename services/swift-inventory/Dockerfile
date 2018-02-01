FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt

SWIFT_AUTH_TOKEN=880eb4cba9e243d3bff2936747afaaa4
python -m dos_connect.apps.inventory.swift_inventory
--dos_server http://0.0.0.0:8080   etl_development

CMD SWIFT_AUTH_TOKEN=$SWIFT_AUTH_TOKEN \
    DOS_API_KEY=$DOS_API_KEY \
    python -m dos_connect.apps.inventory.swift_inventory \
    --dos_server $DOS_SERVER \
    --endpoint_url $SWIFT_ENDPOINT_URL \
    $OBSERVER_PARMS \
    $SWIFT_BUCKET \
