FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive
ENV container docker

RUN apt-get clean; apt-get update -y;
RUN echo 'APT::Install-Recommends "0"; \n\
APT::Get::Assume-Yes "true"; \n\
APT::Install-Suggests "0";' > /etc/apt/apt.conf.d/01buildconfig


RUN apt-get install -y \
    apache2 \
    asciidoc \
    acl \
    bzip2 \
    cdbs \
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
    mercurial \
    mysql-server \
    openssh-client \
    openssh-server \
    python-dbus \
    reprepro \
    rsync \
    ruby \
    subversion \
    sudo \
    unzip \
    zip \
    xsltproc \
    python-coverage \
    python-httplib2 \
    python-jinja2 \
    python-keyczar \
    python-mock \
    python-mysqldb \
    python-nose \
    python-paramiko \
    python-pip \
    python-setuptools \
    python-virtualenv \
    virtualenv \
    python-yaml

# some tests assume the .deb is cached
RUN rm /etc/apt/apt.conf.d/docker-clean

RUN locale-gen en_US.UTF-8
RUN ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
    cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys && \
    for key in /etc/ssh/ssh_host_*_key.pub; do echo "localhost $(cat ${key})" >> /root/.ssh/known_hosts; done

RUN mkdir /etc/ansible/
RUN /bin/echo -e "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts

VOLUME /sys/fs/cgroup /run/lock /run /tmp
CMD ["/sbin/init"]
