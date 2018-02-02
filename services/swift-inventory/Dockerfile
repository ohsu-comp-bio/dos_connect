FROM python:2.7
COPY *.* /
COPY services /services
COPY dos_connect /dos_connect
RUN pip install -r requirements.txt

CMD /services/swift-inventory/inventory-and-sleep.sh
