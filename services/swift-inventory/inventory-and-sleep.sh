#!/bin/bash
# infinite loop
while :
do
  python -m dos_connect.apps.inventory.swift_inventory \
    --dos_server $DOS_SERVER     $OBSERVER_PARMS     $BUCKET_NAME
  sleep $SLEEP
done
