FROM ubuntu:14.04

ARG PACKAGES='\
    memcached \
    python-memcache \
    python-keystoneclient \
    python-swiftclient \
    python-swiftclient \
    python-netifaces \
    python-xattr \
    rsync \
    supervisor \
    swift \
    swift-proxy \
    swift-object \
    swift-account \
    swift-plugin-s3 \
    swift-container \
    curl \
    wget'

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends $PACKAGES

    
RUN mkdir -p /var/log/supervisor
COPY files/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY files/swift.conf            /etc/swift/swift.conf
COPY files/proxy-server.conf     /etc/swift/proxy-server.conf
COPY files/account-server.conf   /etc/swift/account-server.conf
COPY files/object-server.conf    /etc/swift/object-server.conf
COPY files/container-server.conf /etc/swift/container-server.conf
COPY files/proxy-server.conf     /etc/swift/proxy-server.conf
COPY files/webhook_notifications.py /usr/lib/python2.7/dist-packages/swift/common/middleware/webhook_notifications.py
COPY files/rsyncd.conf           /etc/rsyncd.conf
COPY files/startmain.sh          /usr/local/bin/startmain.sh

RUN chmod 755 /usr/local/bin/*.sh
EXPOSE 8080

CMD /usr/local/bin/startmain.sh
