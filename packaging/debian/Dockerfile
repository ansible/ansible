FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
    asciidoc \
    cdbs \
    debootstrap \
    devscripts \
    make \
    pbuilder \
    python-setuptools

VOLUME /ansible
WORKDIR /ansible

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["make deb"]
