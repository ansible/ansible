FROM opensuse:42.2

RUN zypper --non-interactive --gpg-auto-import-keys refresh && \
    zypper --non-interactive install --force systemd-sysvinit && \
    zypper --non-interactive install --auto-agree-with-licenses --no-recommends \
    acl \
    apache2 \
    asciidoc \
    bzip2 \
    curl \
    dbus-1-python \
    gcc \
    git \
    glibc-i18ndata \
    glibc-locale \
    iproute2 \
    lsb-release \
    make \
    mariadb \
    mercurial \
    openssh \
    postgresql-server \
    python-cryptography \
    python-devel \
    python-httplib2 \
    python-jinja2 \
    python-keyczar \
    python-lxml \
    python-mock \
    python-MySQL-python \
    python-nose \
    python-paramiko \
    python-passlib \
    python-pip \
    python-psycopg2 \
    python-PyYAML \
    python-setuptools \
    python-virtualenv \
    rpm-build \
    ruby \
    sshpass \
    subversion \
    sudo \
    tar \
    unzip \
    which \
    zip \
    && \
    zypper clean

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
RUN pip install coverage junit-xml
ENV container=docker
CMD ["/sbin/init"]
