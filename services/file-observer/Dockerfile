FROM python:2.7
COPY *.* /
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt
CMD DOS_API_KEY=$DOS_API_KEY python -m dos_connect.apps.observers.file_observer \
--dos_server $DOS_SERVER \
$OBSERVER_PARMS $MONITOR_DIRECTORY
