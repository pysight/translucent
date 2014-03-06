.. image:: https://travis-ci.org/pysight/translucent.png
	:target: https://travis-ci.org/pysight/translucent
	
Installing for Development
==========================

Install the Python package in development mode:

.. code-block:: bash

	$ python setup.py develop

Note: in what follows, ``npm`` command line tool is assumed to be installed (a standard part of ``node.js`` distribution).

Install ``grunt`` and ``bower`` globally:

.. code-block:: bash

	$ npm install -g grunt grunt-cli bower

Install node and bower dependencies:

.. code-block:: bash

	$ npm install
	$ bower install

Build ``vendor.js`` and ``vendor.css``:

.. code-block:: bash

	$ grunt dist

Build ``app.js`` and ``style.css``:

.. code-block:: bash

	$ grunt build

To launch ``grunt`` in development mode (watches ``*.coffee`` and ``*.styl`` files and rebuilds ``app.js`` and ``style.css`` as needed), run:

.. code-block:: bash

	$ grunt dev

To run the Python test suite, assuming `tox` and `pytest` are installed:

.. code-block:: bash

	$ tox -e check
