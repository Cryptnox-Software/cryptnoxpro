=============
Cryptnox Card
=============

.. image:: https://img.shields.io/pypi/v/cryptnoxcard
    :target: https://pypi.org/project/cryptnoxcard


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

Exit input
^^^^^^^^^^

Whenever an input is requested from the user: PIN or PUK code or any other information,
the command execution can be exited with the keyword ``exit``. When this is used the
command stops the execution.

To not overcrowd the interface this is not mentioned when information is requested by
the CLI.

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

Seed generation
---------------

There are several ways to populate a card with a seed.

Those that need entropy use the random number generator on the card.


Backup
^^^^^^

To use this way of creating a seed access to `AWS <https://aws.amazon.com>`_ is required.
It is out of the scope of this documentation how to acquire **Access Key ID** and **Secret Access Key**
from the AWS as it's a third party service and may change.

After getting the entropy from the card the user is asked for AWS access keys, two regions and a
name for the backup. Two regions are used for using KMS and Secrets Manager services on two
separate machines to increase the security of the saved entropy. Name of the backup is used to
identify which entropy will be restored with the Restore command.

The backed up information is retrieved for comparison with the original to make sure the saving
process was successful and next time when the data is retrieved is the same as the entropy that is
us for seed generation for the card. After this the seed is uploaded to the card.

After the operation a summary will be shown and saved to a file with the name of the regions and
name of the backup.

This is safe way to store the entropy as the information for recreating is saved in the cloud in
two separate regions chosen by the user. It is also simpler then requesting from the user to secure
the mnemonic.

Dual Initialization
^^^^^^^^^^^^^^^^^^^

For this process two Cryptnox Cards are required. The seed is generated in both cards in a secure
way. You will need to start the command with the first card for the host to get information from it.
After that the user is asked to remove the card and insert the second card into the same reader.
The information from the first card will be injected into the second card and a seed is generated
in the second card at this point. The process is not finished. Information will be requested
from second card and the user needs to remove the second card and insert the first card into
the same reader. The information from the second card will be injected into the first card. At
this time the first card will use the information to generate the same seed the second card has
already generated. When the process has finished the two card will have the same seed in them
and have access to the same accounts.

This is the most secure way to generate a seed while still having a backup. The seed newer leaves
the card. The common information is used for it's generation, but the information that was received
from the card in the process is not enough to generate the seed.

Recover
^^^^^^^

Create seed from the mnemonic, `BIP39 <https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki>`_,
entered by the user and upload it onto the card. This mnemonic could be acquired by using the
command Upload.

Restore
^^^^^^^

To use this way of creating a seed access to `AWS <https://aws.amazon.com>`_ is required.
It is out of the scope of this documentation how to acquire **Access Key ID** and **Secret Access Key**
from the AWS as it's a third party service and may change.

If a Backup operation has been finished this command allows for retrieval of the entropy and it's
usage in populating a card with a seed. The user will be asked for AWS access keys, two regions
and the name of the backup to be retrieved. The host tries to acquire the backup from the two given
regions under the given name. The retrieved information is used to generate a seed that is uploaded
to the card.

Upload
^^^^^^

Get the entropy from the card. Generate mnemonic
`BIP39 <https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki>`_ and seed on the host.
Upload the seed to the card. Show the mnemonic to the user for saving it, on a paper or electronic
form for later recovery.

With the mnemonic the seed can be generated by anyone and access to funds connected to accounts
gained. It is the responsibility of the user to keep the mnemonic safe and secure.

If the mnemonic is lost there is no way to recover the account and funds connected to it.
