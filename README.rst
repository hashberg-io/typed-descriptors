
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

Classes from the ``typed_descriptors`` module can be used to create statically typechecked descriptors which implement the following features:

- attributes with runtime typechecking on write
- attributes with validation on write
- readonly attributes (set once)
- cached properties

Typechecking is compatible with `PEP 484 type hints <https://www.python.org/dev/peps/pep-0484/>`_.
Runtime typechecking is performed by the `typing-validation <https://github.com/hashberg-io/typing-validation>`_ library.

Below is a simple example displaying all features listed above:

.. code-block:: python

    from collections.abc import Sequence
    import networkx as nx # type: ignore
    from typed_descriptors import Attr, Prop

    class LabelledKn:
        r"""
            A complete graph :math:`K_n` with readonly size and mutable labels,
            where the NetworkX graph object is computed lazily and cached.
        """

        n = Attr(int, lambda self, n: n >= 0, readonly=True)
        #   type ^^^       validation ^^^^^^  ^^^^^^^^^^^^^ attribute is readonly

        labels = Attr(Sequence[str], lambda self, labels: len(labels) == self.n)
        #        type ^^^^^^^^^^^^^            validation ^^^^^^^^^^^^^^^^^^^^^

        graph = Prop(nx.Graph, lambda self: nx.complete_graph(self.n))
        #       type ^^^^^^^^    prop value ^^^^^^^^^^^^^^^^^^^^^^^^^

        def __init__(self, n: int, labels: Sequence[int]):
            # Setters for Attr instances take care of runtime typechecking and validation
            # for the arguments 'n' and 'labels' which have been passed to the constuctor.
            self.n = n
            self.labels = labels

    myobj = LabelledKn(3, ["a", "b", "c"])    # OK
    myobj.labels = ("x", "y", "z")            # OK
    print(myobj.graph.edges)                  # OK: EdgeView([(0, 1), (0, 2), (1, 2)])

    myobj.x = 5                               # AttributeError (readonly descriptor)
    myobj.y = ["a", "b", "c", "d"]            # ValueError (lenght of y is not 3)
    myobj.y = 5                               # TypeError (type of y is not 'Sequence')
    myobj.y = [2, 3, 5]                       # TypeError (type of y is not 'Sequence[str]')


API
---

For the full API documentation, see https://typed-descriptors.readthedocs.io/


Contributing
------------

Please see `<CONTRIBUTING.md>`_.


License
-------

`MIT © Hashberg Ltd. <LICENSE>`_
