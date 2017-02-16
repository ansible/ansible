FROM ubuntu:16.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    acl \
    apache2 \
    bzip2 \
    curl \
    debhelper \
    debianutils \
    devscripts \
    docbook-xml \
    dpkg-dev \
    fakeroot \
    gawk \
    git \
    iproute2 \
    libxml2-utils \
    locales \
    lsb-release \
    make \
    mysql-server \
    openssh-client \
    openssh-server \
    python3-coverage \
    python3-dbus \
    python3-httplib2 \
    python3-jinja2 \
    python3-mock \
    python3-mysqldb \
    python3-nose \
    python3-paramiko \
    python3-passlib \
    python3-pip \
    python3-setuptools \
    python3-virtualenv \
    python3-wheel \
    python3-yaml \
    reprepro \
    rsync \
    ruby \
    subversion \
    sudo \
    unzip \
    virtualenv \
    xsltproc \
    zip \
    && \
    apt-get clean

RUN rm /etc/apt/apt.conf.d/docker-clean
RUN mkdir /etc/ansible/
RUN /bin/echo -e "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts
RUN locale-gen en_US.UTF-8
RUN ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
    cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys && \
    for key in /etc/ssh/ssh_host_*_key.pub; do echo "localhost $(cat ${key})" >> /root/.ssh/known_hosts; done
VOLUME /sys/fs/cgroup /run/lock /run /tmp
RUN pip3 install junit-xml python3-keyczar
ENV container=docker
CMD ["/sbin/init"]
