:orphan:

update-bundled
==============

Check whether any of our known bundled code needs to be updated for a new upstream release.

This test can error in the following ways:

* The bundled code is out of date with regard to the latest release on pypi.  Update the code
  to the new version and update the version in _BUNDLED_METADATA to solve this.

* The code is lacking a _BUNDLED_METADATA variable.  This typically happens when a bundled version
  is updated and we forget to add a _BUNDLED_METADATA variable to the updated file.  Once that is
  added, this error should go away.

* A file has a _BUNDLED_METADATA variable but the file isn't specified in
  :file:`test/sanity/code-smell/update-bundled.py`.  This typically happens when a new bundled
  library is added.  Add the file to the `get_bundled_libs()` function in the `update-bundled.py`
  test script to solve this error.

_BUNDLED_METADATA has the following fields:

:pypi_name: Name of the bundled package on pypi

:version: Version of the package that we are including here

:version_constraints: Optional PEP440 specifier for the version range that we are bundling.
                      Currently, the only valid use of this is to follow a version that is
                      compatible with the Python stdlib when newer versions of the pypi package
                      implement a new API.
