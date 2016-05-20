# Latest version of centos
FROM centos:centos6
RUN yum -y update; yum clean all;
RUN yum -y install \
    acl \
    asciidoc \
    bzip2 \
    epel-release \
    file \
    gcc \
    git \
    make \
    mercurial \
    mysql \
    mysql-server \
    MySQL-python \
    rpm-build \
    rubygems \
    sed \
    subversion \
    sudo \
    unzip \
    openssh-clients \
    openssh-server \
    which \
    zip
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
RUN ssh-keygen -q -t rsa1 -N '' -f /etc/ssh/ssh_host_key && \
    ssh-keygen -q -t dsa -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ssh-keygen -q -t rsa -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
    cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys && \
    for key in /etc/ssh/ssh_host_*_key.pub; do echo "localhost $(cat ${key})" >> /root/.ssh/known_hosts; done
ENV container=docker
CMD ["/sbin/init"]
