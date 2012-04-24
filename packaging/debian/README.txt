I have added a debian folder for use in building a .deb file for ansible. From the ansible directory you can run the following command to construct a debian package of ansible.

~/ansible$ dpkg-buildpackage -us -uc -rfakeroot

The debian package files will be placed in the ../ directory and can be installed with the following command:
~/$ sudo dpkg -i .deb

Dpkg -i doesn't resolve dependencies, so if the previous command fails because of dependencies, you will need to run the following to install the dependencies (if needed) and then re-run the dpkg -i command to install the package:
$ sudo apt-get -f install

--Henry Graham
