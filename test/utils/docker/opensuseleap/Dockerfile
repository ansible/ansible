FROM opensuse:leap

RUN zypper --gpg-auto-import-keys --non-interactive ref && \
    zypper --gpg-auto-import-keys --non-interactive up

#RUN yum -y update; yum clean all; yum -y swap fakesystemd systemd

RUN zypper --non-interactive install --auto-agree-with-licenses \
    acl \
    asciidoc \
    bzip2 \
    dbus-1-python \
    gcc \
    git \
    glibc-locale \
    iproute \
    lsb-release \
    make \
    mercurial \
    mariadb \
    python-mysql \
    openssh \
    rpm-build \
    ruby \
    subversion \
    sudo \
    tar \
    unzip \
    which \
    zip \
    python-PyYAML \
    python-coverage \
    python-httplib2 \
    python-jinja2 \
    python-keyczar \
    python-mock \
    python-nose \
    python-paramiko \
    python-pip \
    python-setuptools \
    python-virtualenv

# systemd path differs from rhel
ENV LIBSYSTEMD=/usr/lib/systemd/system
RUN (cd ${LIBSYSTEMD}/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f ${LIBSYSTEMD}/multi-user.target.wants/*; \
rm -f /etc/systemd/system/*.wants/*; \
rm -f ${LIBSYSTEMD}/local-fs.target.wants/*; \
rm -f ${LIBSYSTEMD}/sockets.target.wants/*udev*; \
rm -f ${LIBSYSTEMD}/sockets.target.wants/*initctl*; \
rm -f ${LIBSYSTEMD}/basic.target.wants/*;

# don't create systemd-session for ssh connections
RUN sed -i /pam_systemd/d /etc/pam.d/common-session-pc

#RUN localedef --quiet -c -i en_US -f UTF-8 en_US.UTF-8
RUN mkdir /etc/ansible/
RUN /usr/bin/echo -e '[local]\nlocalhost ansible_connection=local' > /etc/ansible/hosts
VOLUME /sys/fs/cgroup /run /tmp
RUN ssh-keygen -q -t rsa1 -N '' -f /etc/ssh/ssh_host_key && \
    ssh-keygen -q -t dsa -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ssh-keygen -q -t rsa -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
    cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys && \
    for key in /etc/ssh/ssh_host_*_key.pub; do echo "localhost $(cat ${key})" >> /root/.ssh/known_hosts; done
# explicitly enable the service, opensuse default to disabled services
RUN systemctl enable sshd.service
ENV container=docker
CMD ["/sbin/init"]
