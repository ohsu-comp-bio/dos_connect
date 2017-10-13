FROM confluentinc/cp-kafka-connect
# see https://docs.confluent.io/current/connect/managing.html#using-community-connectors
RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y maven
RUN apt-get install -y vim
VOLUME ["/jars"]

ENV GRADLE_HOME /opt/gradle
ENV GRADLE_VERSION 4.2.1

ARG GRADLE_DOWNLOAD_SHA256=b551cc04f2ca51c78dd14edb060621f0e5439bdfafa6fd167032a09ac708fbc0
RUN set -o errexit -o nounset \
  && echo "Downloading Gradle" \
  && wget --no-verbose --output-document=gradle.zip "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" \
  \
  && echo "Checking download hash" \
  && echo "${GRADLE_DOWNLOAD_SHA256} *gradle.zip" | sha256sum --check - \
  \
  && echo "Installing Gradle" \
  && unzip gradle.zip \
  && rm gradle.zip \
  && mv "gradle-${GRADLE_VERSION}" "${GRADLE_HOME}/" \
  && ln --symbolic "${GRADLE_HOME}/bin/gradle" /usr/bin/gradle \
  \
  && echo "Adding gradle user and group" \
  && groupadd --system --gid 1000 gradle \
  && useradd --system --gid gradle --uid 1000 --shell /bin/bash --create-home gradle \
  && mkdir /home/gradle/.gradle \
  && chown --recursive gradle:gradle /home/gradle \
  \
  && echo "Symlinking root Gradle cache to gradle Gradle cache" \
  && ln -s /home/gradle/.gradle /root/.gradle

# build one connector to prime maven's repo with commonly used jars
RUN git clone https://github.com/ohsu-comp-bio/kafka-connect-directory-source.git
WORKDIR kafka-connect-directory-source
RUN git checkout -b s3
RUN git pull origin s3
#RUN mvn clean
#RUN mvn package -Dmaven.test.skip=true
# see https://docs.confluent.io/current/connect/userguide.html#running-workers
RUN gradle shadowJar

