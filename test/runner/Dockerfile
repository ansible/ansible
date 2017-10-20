FROM ubuntu:16.04

COPY docker/deadsnakes.list /etc/apt/sources.list.d/deadsnakes.list

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gcc \
    git \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    locales \
    make \
    openssh-client \
    openssl \
    python2.6-dev \
    python2.7-dev \
    python3.5-dev \
    python3.6-dev \
    shellcheck \
    && \
    apt-get clean

RUN rm /etc/apt/apt.conf.d/docker-clean
RUN locale-gen en_US.UTF-8
VOLUME /sys/fs/cgroup /run/lock /run /tmp

ADD https://bootstrap.pypa.io/get-pip.py /tmp/get-pip.py

COPY requirements/*.txt /tmp/requirements/
COPY docker/requirements.sh /tmp/
RUN cd /tmp/requirements && /tmp/requirements.sh

RUN ln -s python2.7 /usr/bin/python2
RUN ln -s python3.6 /usr/bin/python3
RUN ln -s python3   /usr/bin/python

ENV container=docker
CMD ["/sbin/init"]
