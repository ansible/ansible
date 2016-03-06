# Latest version of centos
FROM centos:centos6
RUN yum -y update; yum clean all; 
RUN yum -y install \
    epel-release \
    file \
    gcc \
    git \
    make \
    mercurial \
    rubygems \
    sed \
    subversion \
    sudo \
    unzip \
    which
RUN yum -y install \
    PyYAML \
    python-coverage \
    python-devel \
    python-httplib2 \
    python-jinja2 \
    python-keyczar \
    python-mock \
    python-nose \
    python-paramiko \
    python-pip \
    python-setuptools \
    python-virtualenv
RUN pip install --upgrade jinja2
RUN rpm -e --nodeps python-crypto; pip install pycrypto
RUN /bin/sed -i -e 's/^\(Defaults\s*requiretty\)/#--- \1/'  /etc/sudoers
RUN mkdir /etc/ansible/
RUN /bin/echo -e '[local]\nlocalhost ansible_connection=local' > /etc/ansible/hosts
#VOLUME /sys/fs/cgroup /run /tmp
ENV container=docker
CMD ["/sbin/init"]
