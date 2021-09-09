=============
Cryptnox Card
=============

**Warning: This is a beta release of the software.
It is released for development purposes.
Use at your own risk.**

A command line user interface to manage and use of `Cryptnox cards <https://www.cryptnox.com/>`_.

This provides basic wallets for `Bitcoin <https://bitcoin.org>`_ and
`Ethereum <https://ethereum.org>`_.

It is able to execute `cleos <https://eos.io/for-developers/build/cleos/>`_ commands and use
the keys on the card for signing.

To buy NFC enabled cards that are supported by this application go to:
`https://www.cryptnox.com/ <https://www.cryptnox.com/>`_

License
-------

The library is available under dual licensing. You can use the library under the
conditions of `GNU GENERAL PUBLIC LICENSE 3.0+ <https://www.gnu.org/licenses/gpl-3.0.en.html>`_
or `contact us <info@cryptnox.ch>`_ to ask about commercial licensing.

Installation and requirements
-----------------------------

The package can be installed using pip package manager with:

.. code-block:: bash

    pip install cryptnoxcard

The application can also be installed from source as python package.
In the root of the project, execute:

.. code-block:: bash

    pip install .

This installs the application into your python packages and makes the
``crytpnoxcard`` available as executable.

If during python installation its path was added to system path the executable,
e.g. command is available system wide.

Windows Microsoft Visual C++ 14.x build tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to install from pip package on windows, because of dependencies you will
have to install Microsoft Visual C++ 14.x build tools that you can download from here:
`https://visualstudio.microsoft.com/visual-cpp-build-tools/ <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_

Linux additional packages
^^^^^^^^^^^^^^^^^^^^^^^^^

On some Debian/Ubuntu Linux systems there binaries for sme libraries are not
delivered with the installed package. In this case install the following tools,
so that they can be compiled during installation process.

.. code-block:: bash

    sudo apt-get install build-essential autoconf libtool pkg-config python3-dev swig libpcsclite-dev

MacOS missing certificates
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're using macOS and the command CLI is showing issues of missing certificates,
open Macintosh HD > Applications > Python3.6 folder (or other version of python you're using) >
double click on **Install Certificates.command** file.

Running the application
-----------------------

The application can receive commands directly in any command line, or can be started in
`Interactive Mode <#interactive-mode>`_ by starting without any arguments or options.
The later will also start if the executable is called from a GUI, like Windows Explorer.

Development environment
-----------------------

For development purposes or for running separately from the system environment
pipenv configuration files are provided.

To set it up, use, from the root folder of the project:

.. code-block:: bash

    pipenv install

or, if you want libraries for development purposes like pylint:

.. code-block:: bash

    pipenv install --dev

To enter the new environment use:

.. code-block:: bash

    pipenv shell

This will open a new terminal inside the one it was called from. From here all
packages will be available to run the application.

From here the CLI is available as a script:

.. code-block:: bash

    python cryptnoxcard/main.py

or as a module:

.. code-block:: bash

    python -m cryptnoxcard.main

Secrets
-------

Each card is protected by two secrets only known to the owner of the card.

PIN code
^^^^^^^^

The PIN code must be 4 to 9 number characters ('0'-'9').
After entering the wrong PIN code 3 times the card PIN code is
locked, and it must be unlocked using the PUK code.

Entering the correct PIN code resets the number of times the wrong PIN code
can be entered.

PUK code
^^^^^^^^

The PUK code must be 15 alphanumerical characters ('a'-'z', 'A'-'Z', '0'-'9').

Demo mode
---------

**Warning:** Only use for testing purposes.

The card can be initialized in demo mode. This is done for convenience of the
user as you don't have to enter the card secrets. For this reason it comes at
the expense of security.

The card is initialized with following infomation:


* Owner name: "DEMO"
* Owner email: "DEMO"
* PIN code 000000000
* PIK code 000000000000

When the application asks for any secret, PIN or PUK code, press "ENTER" key.
The application will use the predefined information to fill it for you.

Demo mode on card is determined from the owner name and email.

Interactive mode
----------------

An interactive mode is available if the command is entered without any arguments
and options.

In this mode the user will get a similar interface as a command line with its
own prompt accepting same commands as regular call.

When the mode starts it will show list of available cards.

The prompt is also showing useful information:


* **cryptnoxcard** indicates that the user is in interactive mode
* Serial number of the selected card on which the command will be executed
* Indication that the card is in demo mode
