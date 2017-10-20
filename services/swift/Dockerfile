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
    wget \
    build-essential autoconf libtool pkg-config python-opengl python-imaging python-pyrex python-pyside.qtopengl idle-python2.7 qt4-dev-tools qt4-designer libqtgui4 libqtcore4 libqt4-xml libqt4-test libqt4-script libqt4-network libqt4-dbus python-qt4 python-qt4-gl libgle3 python-dev'

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends $PACKAGES

    
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
RUN pip install -U setuptools pip
RUN pip install python-openstackclient



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
