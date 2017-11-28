# Building pyfomod's deb package

This is a document written for when I inevitably forget all about
this debian/ubuntu packaging business and start panicking.

Even though this is taylored to *pyfomod* it can easily be used with
any python package that needs to be deployed to a PPA in Launchpad.

I use globbing a LOT in this doc but you should just use the proper
file/folder names.

Remember:

- upstream == source package


## Setup

```
sudo apt install gnupg pbuilder ubuntu-dev-tools apt-file debmake
```

Follow procedures [here](http://packaging.ubuntu.com/html/getting-set-up.html)
to setup GPG and SSH keys, pbuilder and Launchpad account.


## Initial files/templates

Should no longer be necessary but kept as a reminder for other
projects.

Either download the upstream tarball and place in this directory or
do a wee trick:

```
git checkout master
rm -rf dist/
python setup.py sdist
git checkout debian
mv dist/* .
```

And now you have the tarball in this directory. Unpack it:

```
tar xf <upstream name>-*.tar.gz
cd <upstream name>-*
```

Initial templates:

```
debmake -b':py3'
```

Two very important things happened - an `orig.tar.gz` file will have
appeared in the parent directory which is a symlink to the upstream
`tar.gz` and a bunch of templates have appeared. You must modify the
following:

- debian/changelog
  - Update the version, to something like
    *<upstream_version>-0ubuntu<release_version>* where
    *release_version* is the release version of this package, not
    upstream. If uploading to multiple distros, use this instead
    *<upstream_version>-0ubuntu<release_version>~<distro>* where
    *distro* is the distribution you're uploading for. You need to
    change the changelog and upload separately for each don't forget!

- debian/rules
  - Literally replace whatever is there with this:
    ```
    export PYBUILD_NAME=<upstream_name>

    %:
            dh $@ --with python2,python3 --buildsystem=pybuild
    ```
    Profit. Obviously replace the name and remove whatever python
    version you don't need.

- debian/control
  - Should be self-explanatory but make sure to keep *Source* as
    the upstream name and *Section* as *python*.
    Build-Depends is for build-time dependencies, that includes
    stuff for testing! (python setup.py test is run by default by
    pybuild)

  - *Package* must start with *python-* or *python3-*.

- debian/copyright
  - Not super important as it won't crash your build but take a look
    at others to see how to do it, it's easy.

- debian/watch
  - If dling from PyPi run:
    ```
    curl -o debian/watch http://pypi.debian.net/mypackage/watch
    ```
  - If from somewhere else,
    [panic](https://www.google.pt/search?q=ubuntu+package+watch+file)


## Building

Finally. At the root of your source directory (the on that contains 
`debian/`) run:

```
debuild
```

And check the logs for errors and warnings. If you're only building
for distros that are not your current one then use pbuilder to test:

```
pbuilder-dist <distro> build ../*.dsc
```

Obviously you should use pbuilder for all distros that are not your
current one.

If you need to use faster builds for testing locally don't sign them:

```
debuild -S -us -uc
```

(Just `-S` does a source build - doesn't build the `.deb`)


## Updating

Update later when I actually do it (oh the irony) but should go
something like this:

```
cd <package_name>-*
uscan
```

*uscan* is magic, don't worry about it. Now I'm not sure whether the
folder you're on is renamed or a new one is made for the new upstream
version, but change to the new one.

```
dch
```

This last one opens up the changelog and let's you edit it. Most
changelogs will be *New upstream version.* so not a problem.


## Uploading

Now rebuild your stuff properly and upload it:

```
debuild -S
cd ..
dput ppa:<username>/<ppa-name> *.changes
```

And wait for two hours while Launchpad builds and publishes your stuff.
