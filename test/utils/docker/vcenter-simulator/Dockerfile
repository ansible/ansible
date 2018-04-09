FROM fedora:26

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*; \
rm -f /etc/systemd/system/*.wants/*; \
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*; \
rm -f /lib/systemd/system/anaconda.target.wants/*;

RUN dnf clean all && \
    dnf -y --setopt=install_weak_deps=false install \
    git \
    glibc \
    gcc \
    golang-bin \
    python-devel \
    python-pip \
    python-setuptools \
    redhat-rpm-config \
    yum \
    && \
    dnf clean all

VOLUME /sys/fs/cgroup /run /tmp
ENV container=docker
RUN mkdir -p /opt/gocode
RUN chmod -R 777 /opt/gocode
ENV GOPATH=/opt/gocode
RUN go get -u github.com/vmware/govmomi/vcsim
RUN go get github.com/vmware/govmomi/govc
RUN pip install psutil
RUN pip install flask
ADD flask_control.py /root/flask_control.py


EXPOSE 5000 8989 443 80 8080
CMD ["/root/flask_control.py"]
