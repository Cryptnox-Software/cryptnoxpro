=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_\ ,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

`Unreleased <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.3.2...HEAD>`_
-------------------------------------------------------------------------------------------

`1.3.2 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.3.1...1.3.2>`_ - 2021-10-13
------------------------------------------------------------------------------------------------

Changed
^^^^^^^

* Ethereum endpoint through cryptnox node updated to use different domains on standard ports
* With ``info`` command for balance show the issue instead of "--"

Fixed
^^^^^

* ``exit`` keyword when input is requested from user, like PIN or PUK code
* Bitcoin sending with multiple inputs is rejected by the node

`1.3.1 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.3.0...1.3.1>`_ - 2021-10-07
------------------------------------------------------------------------------------------------

Fixed
^^^^^

* Crash when calling config under currencies

`1.3.0 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.2.0...1.3.0>`_ - 2021-10-06
------------------------------------------------------------------------------------------------

Added
^^^^^

* card_config can update the status of PIN-less path and PIN authentication.

Changed
^^^^^^^

* Configuration is saved into the card instead of a file.

Fixed
^^^^^

* When waiting for card after card is detected the application crashes.
* Ethereum network name conversion

`1.2.0 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.1.0...1.2.0>`_ - 2021-09-16
------------------------------------------------------------------------------------------------

Added
^^^^^

* New endpoint for Ethereum network used by default. User can still the infura network with a project key

Changed
^^^^^^^

* Ordering in config command to BTC, ETH, EOS.
* When changing PIN or PUK code message made clear that the card is not initialized.
* Resetting uninitialized card message updated.
* User key check if card is initialized before continuing.
* In change_puk check current PUK before asking for new one.
* Show warning on command if card origin is unknown or fake instead of exiting command.

Fixed
^^^^^

* In demo mode when asked for PUK code, entering anything will go into loop asking for the code.
* There is no message when adding piv, but piv is not present

`1.1.0 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.0.2...1.1.0>`_ - 2021-09-16
------------------------------------------------------------------------------------------------

Added
^^^^^

* Backup and restore of entropy for seed generation to KMS in HSM.


`1.0.2 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.0.1...1.0.2>`_ - 2021-09-09
------------------------------------------------------------------------------------------------

Changed
^^^^^^^

* Improve setup process.


`1.0.1 <https://github.com/Cryptnox-Software/cryptnoxcard/compare/v1.0.0...1.0.1>`_ - 2021-08-20
------------------------------------------------------------------------------------------------

Fixed
^^^^^

* Update package on PiPI.

`1.0.0 <https://github.com/Cryptnox-Software/cryptnoxcard/releases/tag/v1.0.0>`_ - 2021-08-20
---------------------------------------------------------------------------------------------

Added
^^^^^

* Command line interface with commands for interacting with Cryptnox cards.
* Interactive mode.
* Pipfile and requirements for setting up environment.
* Setup file to install the library.
