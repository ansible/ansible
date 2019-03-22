from sys import argv
from subprocess import Popen, PIPE, STDOUT

p = Popen(["openssl", "s_client", "-host", argv[1], "-port", "443", "-prexit", "-showcerts"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
stdout = p.communicate(input=b'\n')[0]
data = stdout.decode()

certs = []
cert = ""
capturing = False
for line in data.split('\n'):
    if line == '-----BEGIN CERTIFICATE-----':
        capturing = True

    if capturing:
        cert = "{0}{1}\n".format(cert, line)

    if line == '-----END CERTIFICATE-----':
        capturing = False
        certs.append(cert)
        cert = ""

with open(argv[2], 'w') as f:
    for cert in set(certs):
        f.write(cert)
