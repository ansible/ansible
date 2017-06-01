FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
    asciidoc \
    cdbs \
    debootstrap \
    devscripts \
    make \
    pbuilder \
    python-pip \
    python-setuptools

RUN pip install Sphinx

VOLUME /ansible
WORKDIR /ansible

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["make deb"]
