# ansible-podman selinux module

On Fedora-derived systems (and possibly others), selinux can prevent podman
from running the way we need it to for our tests to work.

Loading this module (hopefully) allows you to
[keep selinux enabled](https://stopdisablingselinux.com/) and still be able to
run our tests.

To use it, just run:

```
./build.sh
```

...which will build the module. Then run:

```
sudo semodule -i ansible-podman.pp
```

to insert and enable the module.
