
typed-descriptors: Descriptor classes with typechecking and validation
======================================================================

.. image:: https://img.shields.io/badge/python-3.8+-green.svg
    :target: https://docs.python.org/3.8/
    :alt: Python versions

.. image:: https://img.shields.io/pypi/v/typed-descriptors.svg
    :target: https://pypi.python.org/pypi/typed-descriptors/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/status/typed-descriptors.svg
    :target: https://pypi.python.org/pypi/typed-descriptors/
    :alt: PyPI status

.. image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: https://github.com/python/mypy
    :alt: Checked with Mypy

.. image:: https://readthedocs.org/projects/typed-descriptors/badge/?version=latest
    :target: https://typed-descriptors.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://github.com/hashberg-io/typed-descriptors/actions/workflows/python-pytest.yml/badge.svg
    :target: https://github.com/hashberg-io/typed-descriptors/actions/workflows/python-pytest.yml
    :alt: Python package status

.. image:: https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square
    :target: https://github.com/RichardLitt/standard-readme
    :alt: standard-readme compliant


typed-descriptors is a small library of descriptor classes featuring static and runtime typechecking, runtime validation, and other useful features.

Static typechecking is compatible with `PEP 484 type hints <https://www.python.org/dev/peps/pep-0484/>`_, and runtime typechecking is performed by the `typing-validation <https://github.com/hashberg-io/typing-validation>`_ library.

.. contents::


Install
-------

You can install the latest release from `PyPI <https://pypi.org/project/typed-descriptors/>`_ as follows:

.. code-block::

    pip install --upgrade typed-descriptors


Usage
-----


API
---

For the full API documentation, see https://typed-descriptors.readthedocs.io/


Contributing
------------

Please see `<CONTRIBUTING.md>`_.


License
-------

`MIT © Hashberg Ltd. <LICENSE>`_
