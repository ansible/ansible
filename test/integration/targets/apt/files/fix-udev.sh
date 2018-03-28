#!/bin/bash

cat > /usr/sbin/policy-rc.d <<EOF
#!/bin/bash
exit 101
EOF
chmod +x /usr/sbin/policy-rc.d
dpkg-divert --local --rename --add /sbin/initctl
ln -s /bin/true /sbin/initctl
