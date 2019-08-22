FROM debian:7.7

MAINTAINER Rob McQueen

# Install Python
RUN apt-get update && apt-get install -y \
  python-dev \
  python-virtualenv \
  sudo

# Install Ansible
RUN mkdir /opt/ansible && virtualenv /opt/ansible/venv && \
  /opt/ansible/venv/bin/pip install ansible

ADD . /build
COPY .ansible-test /build
WORKDIR /build

CMD /opt/ansible/venv/bin/ansible-playbook -i inventory.yml \
    -c local -s -e testing=true -e role=$DOCKER_TEST_ROLE \
    --docker fedora29 -v shippable/ playbook.yml; /bin/bash