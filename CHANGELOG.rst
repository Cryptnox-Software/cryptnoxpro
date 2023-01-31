=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_\ ,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

`Unreleased <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.7.0...HEAD>`_
--------------------------------------------------------------------------------------

`2.8.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.7.0...v2.8.0>`_ - 2022-01-31
------------------------------------------------------------------------------------------------

Added
^^^^^

- Option to start a server and access the card remotely

`2.7.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.6.0...v2.7.0>`_ - 2022-11-28
------------------------------------------------------------------------------------------------

Added
^^^^^

- Card can be opened with AWS KMS key instead of PIN code
- Option to backup to cloud when seed is uploaded or recovered

`2.6.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.5.0...v2.6.0>`_ - 2022-09-30
------------------------------------------------------------------------------------------------

Added
^^^^^

- ERC1155 contract ABI to system for selection for use

Fixed
^^^^^

- `eosio` command `get` subcommand help not shown

`2.5.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.4.0...v2.5.0>`_ - 2022-08-11
------------------------------------------------------------------------------------------------

Added
^^^^^

- Default servers for AWS backup and restore
- Default randomized alias for AWS backup
- Use `rootkey.csv` file from download folder for AWS backup and restore, delete credentials after operation

Changed
^^^^^^^

- In case of exception write the error log into user folder instead of installation folder

Fixed
^^^^^

- Missing word for retrying PIN code
- Seed phrase of length other than 12 or 24 words is accepted by the system

`2.4.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.3.0...v2.4.0>`_ - 2022-07-19
------------------------------------------------------------------------------------------------

Added
^^^^^

- Python 3.10 support
- For NFT cards abi url parsing

Removed
^^^^^^^

- Python 3.6 support

Fixed
^^^^^

- Application crashing when using current key with derivation path

`2.3.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.2.2...v2.3.0>`_ - 2022-06-07
------------------------------------------------------------------------------------------------

Added
^^^^^

- Remote mode for connecting over a port

Changed
^^^^^^^

- Installation instructions added missing instructions

`2.2.2 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.2.1...v2.2.2>`_ - 2022-03-17
------------------------------------------------------------------------------------------------

Fixed
^^^^^

* Init not finished with NFT card when ABI is large

`2.2.1 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.2.0...v2.2.1>`_ - 2022-03-14
------------------------------------------------------------------------------------------------

Fixed
^^^^^

* Application crashes when initializing NFT card
* Help not show on some commands
* List of cards is doubled when executing list command
* Seed backup to KMS name of backup error message not clear enough
* Card not reloaded after dual seed generation
* Application crashes during dual seed generation while waiting for second card

`2.2.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.1.0...v2.2.0>`_ - 2022-01-31
------------------------------------------------------------------------------------------------

Changed
^^^^^^^

* Combined two scripts into one
* Demo mode renamed to easy mode
* Application name changed to Cryptnox Pro

Fixed
^^^^^

* Error handling while waiting for card when timeout is exceeded
* Error handling when a user enters value for mnemonic that is invalid for BIP39
* Input for user key description to allow numbers and letters
* Crash when showing seed backup options for AWS server

`2.1.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v2.0.0...v2.1.0>`_ - 2022-01-04
------------------------------------------------------------------------------------------------

Added
^^^^^

* Separate CLI for working with NFT cards
* eht command contract parameter to send ERC20 tokens

Fixed
^^^^^

* Exception handling in multiple places.

`2.0.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.3.2...v2.0.0>`_ - 2021-10-13
------------------------------------------------------------------------------------------------

Added
^^^^^

* Dynamic fee calculation for Bitcoin and Ethereum networks

Changed
^^^^^^^

* Recovering seed from mnemonic compliant with BIP39
* Derivation paths to be compliant with BIP44

Fixed
^^^^^

* Send/transfer memo for EOSIO
* Signing multi-input transaction for BTC with user key
* Precision of amounts for sending
* AWS backup wrong credentials crash the application
* verbose option is not doing anything
* EOS transfer doesn't use sender but behaves as send command


`1.3.2 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.3.1...v1.3.2>`_ - 2021-10-13
------------------------------------------------------------------------------------------------

Changed
^^^^^^^

* Ethereum endpoint through cryptnox node updated to use different domains on standard ports
* With ``info`` command for balance show the issue instead of "--"

Fixed
^^^^^

* ``exit`` keyword when input is requested from user, like PIN or PUK code
* Bitcoin sending with multiple inputs is rejected by the node

`1.3.1 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.3.0...v1.3.1>`_ - 2021-10-07
------------------------------------------------------------------------------------------------

Fixed
^^^^^

* Crash when calling config under currencies

`1.3.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.2.0...v1.3.0>`_ - 2021-10-06
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

`1.2.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.1.0...v1.2.0>`_ - 2021-09-16
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

`1.1.0 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.0.2...v1.1.0>`_ - 2021-09-16
------------------------------------------------------------------------------------------------

Added
^^^^^

* Backup and restore of entropy for seed generation to KMS in HSM.


`1.0.2 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.0.1...v1.0.2>`_ - 2021-09-09
------------------------------------------------------------------------------------------------

Changed
^^^^^^^

* Improve setup process.


`1.0.1 <https://github.com/Cryptnox-Software/cryptnoxpro/compare/v1.0.0...v1.0.1>`_ - 2021-08-20
------------------------------------------------------------------------------------------------

Fixed
^^^^^

* Update package on PiPI.

`1.0.0 <https://github.com/Cryptnox-Software/cryptnoxpro/releases/tag/v1.0.0>`_ - 2021-08-20
---------------------------------------------------------------------------------------------

Added
^^^^^

* Command line interface with commands for interacting with Cryptnox cards.
* Interactive mode.
* Pipfile and requirements for setting up environment.
* Setup file to install the library.
