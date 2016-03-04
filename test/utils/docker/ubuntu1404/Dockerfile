FROM ubuntu:trusty
RUN apt-get clean; apt-get update -y;
RUN apt-get install -y \
    debianutils \
    git \
    locales \
    make \
    mercurial \
    ruby \
    subversion \
    sudo \
    unzip
RUN apt-get install -y \
    python-coverage \
    python-httplib2 \
    python-jinja2 \
    python-keyczar \
    python-mock \
    python-nose \
    python-paramiko \
    python-pip \
    python-setuptools \
    python-virtualenv \
    python-yaml
RUN sed -i -e 's/^\(Defaults\s*requiretty\)/#--- \1/'  /etc/sudoers
RUN mkdir /etc/ansible/
RUN echo -e '[local]\nlocalhost ansible_connection=local' > /etc/ansible/hosts
RUN locale-gen en_US.UTF-8
ENV container=docker
CMD ["/sbin/init"]
