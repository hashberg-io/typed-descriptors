
Getting Started
===============

.. _installation:

Installation
------------

You can install the latest release from PyPI as follows:

.. code-block:: console

    $ pip install --upgrade typed-descriptors


.. _usage:

Usage
-----

Classes from the :mod:`typed_descriptors` module can be used to create statically typechecked descriptors which implement the following features:

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

GitHub repo: https://github.com/hashberg-io/typed-descriptors
