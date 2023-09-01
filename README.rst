openedx-userapi
#############################

|pypi-badge| |ci-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge| |status-badge|

Purpose
*******

API for managing users

OpenEDX does not contain a proper API to create users and make sure you can disable
public registration while still allowing your own users to use the platform.

This projects adds the required API endpoints to create users.

Getting Started
***************

Developing
==========

One Time Setup
--------------
.. code-block::

  # Clone the repository
  git clone git@github.com:makerspace-darmstadt/openedx-userapi.git
  cd openedx-userapi

  # Set up a virtualenv with the same name as the repo and activate it
  # Here's how you might do that if you have virtualenvwrapper setup.
  mkvirtualenv -p python3.8 openedx-userapi


Every time you develop something in this repo
---------------------------------------------
.. code-block::

  # Activate the virtualenv
  # Here's how you might do that if you're using virtualenvwrapper.
  workon openedx-userapi

  # Grab the latest code
  git checkout main
  git pull

  # Install/update the dev requirements
  make requirements

  # Run the tests and quality checks (to verify the status before you make any changes)
  make validate

  # Make a new branch for your changes
  git checkout -b <your_github_username>/<short_description>

  # Using your favorite editor, edit the code to make your change.
  vim ...

  # Run your new tests
  pytest ./path/to/new/tests

  # Run all the tests and quality checks
  make validate

  # Commit all your changes
  git commit ...
  git push

  # Open a PR and ask for review.

Deploying
=========

Simply add this plugin to your config:

```
tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS=git+https://github.com/makerspace-darmstadt/openedx-userapi.git@v0.0.3
 
# Danach container neu bauen
tutor images build openedx
```

.. |pypi-badge| image:: https://img.shields.io/pypi/v/openedx-userapi.svg
    :target: https://pypi.python.org/pypi/openedx-userapi/
    :alt: PyPI

.. |ci-badge| image:: https://github.com/makerspace-darmstadt/openedx-userapi/workflows/Python%20CI/badge.svg?branch=main
    :target: https://github.com/makerspace-darmstadt/openedx-userapi/actions
    :alt: CI

.. |codecov-badge| image:: https://codecov.io/github/makerspace-darmstadt/openedx-userapi/coverage.svg?branch=main
    :target: https://codecov.io/github/makerspace-darmstadt/openedx-userapi?branch=main
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/openedx-userapi/badge/?version=latest
    :target: https://docs.openedx.org/projects/openedx-userapi
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/openedx-userapi.svg
    :target: https://pypi.python.org/pypi/openedx-userapi/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/makerspace-darmstadt/openedx-userapi.svg
    :target: https://github.com/makerspace-darmstadt/openedx-userapi/blob/main/LICENSE.txt
    :alt: License

.. TODO: Choose one of the statuses below and remove the other status-badge lines.
.. |status-badge| image:: https://img.shields.io/badge/Status-Experimental-yellow
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Deprecated-orange
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Unsupported-red
