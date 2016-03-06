# Latest version of centos
FROM fedora:23
RUN dnf -y update; dnf clean all
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*; \
rm -f /etc/systemd/system/*.wants/*; \
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*; \
rm -f /lib/systemd/system/anaconda.target.wants/*;
RUN dnf -y install \
    dbus-python \
    file \
    findutils \
    glibc-common \
    git \
    make \
    mercurial \
    procps \
    PyYAML \
    python-coverage \
    python2-dnf \
    python-httplib2 \
    python-jinja2 \
    python-keyczar \
    python-mock \
    python-nose \
    python-paramiko \
    python-pip \
    python-setuptools \
    python-virtualenv \
    rubygems \
    subversion \
    sudo \
    tar \
    unzip \
    which \
    yum
RUN localedef --quiet -f ISO-8859-1 -i pt_BR pt_BR
RUN localedef --quiet -f ISO-8859-1 -i es_MX es_MX
RUN /usr/bin/sed -i -e 's/^\(Defaults\s*requiretty\)/#--- \1/'  /etc/sudoers
RUN mkdir /etc/ansible/
RUN /usr/bin/echo -e '[local]\nlocalhost ansible_connection=local' > /etc/ansible/hosts
VOLUME /sys/fs/cgroup /run /tmp
ENV container=docker
CMD ["/usr/sbin/init"]
