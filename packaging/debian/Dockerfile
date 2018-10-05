FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
    python-docutils \
    cdbs \
    debootstrap \
    devscripts \
    make \
    pbuilder \
    python-jinja2 \
    python-setuptools \
    python-yaml \
    && \
    apt-get clean

VOLUME /ansible
WORKDIR /ansible

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["make deb"]
