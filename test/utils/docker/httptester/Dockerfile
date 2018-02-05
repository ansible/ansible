FROM nginx:alpine

RUN set -x && \
    apk add -U openssl py-pip && \
    mkdir -p /root/ca/certs /root/ca/private /root/ca/newcerts && \
    echo 1000 > /root/ca/serial && \
    touch /root/ca/index.txt && \
    sed -i 's/\.\/demoCA/\/root\/ca/g' /etc/ssl/openssl.cnf && \
    openssl req -new -x509 -days 3650 -nodes -extensions v3_ca -keyout /root/ca/private/cakey.pem -out /root/ca/cacert.pem \
        -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/CN=ansible.http.tests" && \
    openssl req -new -nodes -out /root/ca/ansible.http.tests-req.pem -keyout /root/ca/private/ansible.http.tests-key.pem \
        -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/CN=ansible.http.tests" && \
    yes | openssl ca -config /etc/ssl/openssl.cnf -days 3650 -out /root/ca/ansible.http.tests-cert.pem -infiles /root/ca/ansible.http.tests-req.pem && \
    openssl req -new -nodes -out /root/ca/sni1.ansible.http.tests-req.pem -keyout /root/ca/private/sni1.ansible.http.tests-key.pem -config /etc/ssl/openssl.cnf \
        -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/CN=sni1.ansible.http.tests" && \
    yes | openssl ca -config /etc/ssl/openssl.cnf -days 3650 -out /root/ca/sni1.ansible.http.tests-cert.pem -infiles /root/ca/sni1.ansible.http.tests-req.pem && \
    openssl req -new -nodes -out /root/ca/sni2.ansible.http.tests-req.pem -keyout /root/ca/private/sni2.ansible.http.tests-key.pem -config /etc/ssl/openssl.cnf \
        -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/CN=sni2.ansible.http.tests" && \
    yes | openssl ca -config /etc/ssl/openssl.cnf -days 3650 -out /root/ca/sni2.ansible.http.tests-cert.pem -infiles /root/ca/sni2.ansible.http.tests-req.pem && \
    openssl req -new -nodes -out /root/ca/client.ansible.http.tests-req.pem -keyout /root/ca/private/client.ansible.http.tests-key.pem -config /etc/ssl/openssl.cnf \
        -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/CN=client.ansible.http.tests" && \
    yes | openssl ca -config /etc/ssl/openssl.cnf -days 3650 -out /root/ca/client.ansible.http.tests-cert.pem -infiles /root/ca/client.ansible.http.tests-req.pem && \
    cp /root/ca/cacert.pem /usr/share/nginx/html/cacert.pem && \
    cp /root/ca/client.ansible.http.tests-cert.pem /usr/share/nginx/html/client.pem && \
    cp /root/ca/private/client.ansible.http.tests-key.pem /usr/share/nginx/html/client.key && \
    pip install gunicorn httpbin==0.5.0

ADD services.sh /services.sh
ADD nginx.sites.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["/services.sh"]
