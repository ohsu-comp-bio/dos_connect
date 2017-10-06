FROM confluentinc/cp-kafka-connect
# see https://docs.confluent.io/current/connect/managing.html#using-community-connectors
RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y maven
VOLUME ["/jars"]
# build one connector to prime maven's repo with commonly used jars
RUN git clone https://github.com/ohsu-comp-bio/kafka-connect-directory-source.git
WORKDIR kafka-connect-directory-source
RUN mvn clean
RUN mvn package
# see https://docs.confluent.io/current/connect/userguide.html#running-workers

