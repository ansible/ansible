#!/bin/bash -exu

src='/root/src'
dst='/root/dst'

mkdir "${src}" "${dst}"
echo "${src} ${dst} None bind 0 0" >> /etc/fstab
cat /etc/fstab
cat /proc/self/mountinfo
mount "${dst}"
cat /etc/fstab
cp /proc/self/mountinfo /tmp/mountinfo
cat /tmp/mountinfo
if [ $(grep --count "${dst}" /tmp/mountinfo) -ne 1 ]; then exit 1; fi
