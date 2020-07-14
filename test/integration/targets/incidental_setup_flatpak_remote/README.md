# Create a dummy flatpak repository remote

This document describes how to create a local flatpak dummy repo. Just like the one contained in the `files/repo.tar.gxz` archive.


## Create a hello world app

Prerequisites:

 - flathub

Prepare the environment:

```
flatpak install --system flathub org.freedesktop.Platform//1.6 org.freedesktop.Sdk//1.6
```

Create a hello world executable:

```
echo $'#!/bin/sh\necho hello world' > hello.sh
```

To create dummy flatpaks, run this (defining a unique NUM for every flatpak to add):

```
export NUM=1
flatpak build-init appdir$NUM com.dummy.App$NUM org.freedesktop.Sdk org.freedesktop.Platform 1.6;
flatpak build appdir$NUM mkdir /app/bin;
flatpak build appdir$NUM install --mode=750 hello.sh /app/bin;
flatpak build-finish --command=hello.sh appdir$NUM
```

## Create a repo and/or add the app to it

Create a repo and add the file to it in one command:

```
flatpak build-export repo appdir$NUM stable
```

## Create flatpak*-files

Put a flatpakref file under the repo folder (`repo/com.dummy.App1.flatpakref`):

```
[Flatpak Ref]
Title=Dummy App$NUM
Name=com.dummy.App$NUM
Branch=stable
Url=file:///tmp/flatpak/repo
GPGKey={{ base64-encoded public KEY }}
IsRuntime=false
RuntimeRepo=https://flathub.org/repo/flathub.flatpakrepo
```

Add a `.flatpakrepo` file to the `repo` folder (`repo/dummy-repo.flatpakrepo`):

```
[Flatpak Repo]
Title=Dummy Repo
Url=file:///tmp/flatpak/repo
Comment=Dummy repo for ansible module integration testing
Description=Dummy repo for ansible module integration testing
GPGKey={{ base64-encoded public KEY }}
```

## Sign the repo

Create a new key in a new gpg home folder (On RedHat systems, the executable needs to addressed as gpg2):

```
mkdir gpg
gpg --homedir gpg --quick-gen-key test@dummy.com
```

Sign the repo and summary file, you need to redo this when you update the repository:

```
flatpak build-sign repo --gpg-sign=KEY_ID --gpg-homedir=gpg
flatpak build-update-repo repo --gpg-sign=KEY_ID --gpg-homedir=gpg
```

Export the public key as a file:

```
gpg --homedir=gpg --export KEY_ID > dummy-repo.gpg
```

Create base64-encoded string from gpg-file for `GPGKey=` property in flatpak*-files:

```
base64 dummy-repo.gpg | tr -d '\n'
```

## How to use the repo

Now you can add the `repo` folder as a local repo:

```
flatpak --system remote-add --gpg-import=/tmp/flatpak/repo/dummy-repo.gpg dummy-repo /tmp/flatpak/repo
```

Or, via `.flatpakrepo` file:

```
flatpak --system remote-add dummy-repo /tmp/flatpak/repo/dummy-repo.flatpakrepo
```

And install the hello world flatpaks like this:

```
flatpak --system install dummy-repo com.dummy.App$NUM
```

Or from flatpakref:

```
flatpak --system install --from /tmp/flatpak/repo/com.dummy.App$NUM.flatpakref
```

Run the app:

```
flatpak run com.dummy.App$NUM
```

To install an app without any runtime dependencies (the app will be broken, but it is enough to test flatpak installation):

```
flatpak --system install --no-deps dummy-repo com.dummy.App$NUM
```

## Sources:

* https://blogs.gnome.org/alexl/2017/02/10/maintaining-a-flatpak-repository/

* http://docs.flatpak.org/en/latest/first-build.html
