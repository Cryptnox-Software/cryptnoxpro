# -*- coding: utf-8 -*-
"""
Module containing command for getting clear public key from the card
"""
import cryptnoxpy
from argparse import Namespace

from .command import Command
from .helper.security import check

try:
    import enums
except ImportError:
    from .. import enums


class GetClearpubkey(Command):
    """
    Command to get the clear public key from the card (without PIN or secure channel)
    """
    _name = "get_clearpubkey"

    def _execute(self, card) -> int:
        """
        Execute the get_clearpubkey command to get clear public key from the card
        
        :param card: The card instance
        :return: 0 if successful, other number indicating an issue
        :rtype: int
        """
        check(card)
        
        try:
            # Get key type from command line arguments, default to K1
            key_type = getattr(self.data, 'key_type', 'K1')
            if isinstance(key_type, str):
                key_type = cryptnoxpy.KeyType[key_type.upper()]
            
            # Get PUK from command line arguments if provided
            puk = getattr(self.data, 'puk', '')
            
            # Get path from command line arguments if provided
            path = getattr(self.data, 'path', '')
            
            # Get compression setting
            compressed = getattr(self.data, 'compressed', True)
            if hasattr(self.data, 'uncompressed') and self.data.uncompressed:
                compressed = False
            
            print("Getting clear public key from card...")
            print(f"Key type: {key_type}")
            print(f"Path: {path if path else cryptnoxpy.Derivation.CURRENT_KEY}")
            print(f"Compressed: {compressed}")
            
            # Enable clear pubkey reading capability if PUK provided
            if puk:
                print("Enabling clear pubkey reading capability...")
                try:
                    # Enable clear pubkey reading (P1=1 in SET PUB EXPORT command)
                    card.set_clearpubkey(True, puk)
                    print("Clear pubkey reading capability enabled")
                except cryptnoxpy.exceptions.PukException as e:
                    print(f"Error: Invalid PUK code - {e}")
                    return -1
                except Exception as e:
                    print(f"Error enabling clear pubkey capability: {e}")
                    return -1
            
            # Calculate derivation parameter
            # For K1: derivation = 0x00 (current key)
            # For R1: derivation = 0x10 (current key R1)
            derivation = 0x00 if key_type == cryptnoxpy.KeyType.K1 else 0x10
            
            try:
                # Get clear public key using get_public_key_clear
                if hasattr(card, 'get_public_key_clear'):
                    # Reset card state before getting public key to avoid session corruption
                    try:
                        # Try to reset the card's derivation state by deriving to a known state
                        if path:
                            card.derive(key_type, path)
                        else:
                            # For current key, derive to a known path first to reset state
                            card.derive(key_type, "m/44'/0'/0'")
                    except Exception:
                        # If derivation fails, continue anyway
                        pass
                    
                    pubkey_bytes = card.get_public_key_clear(derivation, path, compressed)
                    
                    # Convert bytes to hex string for display
                    pubkey_hex = pubkey_bytes.hex()
                    
                    print(f"\nClear Public Key Retrieved:")
                    print(f"Key Type: {key_type.name}")
                    print(f"Format: {'Compressed' if compressed else 'Uncompressed'}")
                    print(f"Length: {len(pubkey_bytes)} bytes")
                    print(f"Public Key: {pubkey_hex}")
                    
                    # Additional format information
                    if len(pubkey_bytes) == 33:
                        print("Format: Compressed (33 bytes)")
                        print("Note: Y-coordinate calculated from X-coordinate using elliptic curve math")
                        print(f"Prefix: 0x{pubkey_bytes[0]:02x} ({'even' if pubkey_bytes[0] == 0x02 else 'odd'} Y-coordinate)")
                    elif len(pubkey_bytes) == 65:
                        print("Format: Uncompressed (65 bytes)")
                        print("Note: Full public key reconstructed from X-coordinate")
                    elif len(pubkey_bytes) == 32:
                        print("Format: X-coordinate only (32 bytes)")
                        print("Note: Card returned only X-coordinate. This is a limitation of the clear channel.")
                    
                else:
                    print("Error: Card does not support clear pubkey reading")
                    print("This feature requires a compatible card firmware version")
                    return -1
                    
            except cryptnoxpy.exceptions.ReadPublicKeyException as e:
                if "6A88" in str(e):
                    print("Error: Clear pubkey reading capability not enabled")
                    print("Please enable it first with: cryptnox get_clearpubkey --puk 'your_puk'")
                elif "6985" in str(e):
                    print("Error: No seed loaded or PIN not verified")
                    print("Please load a seed first: cryptnox seed")
                elif "X-coordinate" in str(e) and "uncompressed" in str(e):
                    print("Error: Cannot get uncompressed public key")
                    print("The card only returns X-coordinate (32 bytes) in clear channel mode.")
                    print("Use --compressed flag to get a compressed public key instead.")
                else:
                    print(f"Error reading clear public key: {e}")
                return -1
            except Exception as e:
                print(f"Unexpected error: {e}")
                return -1
            
            return 0
            
        except cryptnoxpy.exceptions.SeedException:
            print("Error: No seed exists on the card. Please initialize the card first.")
            print("Run: cryptnox init")
            return -1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return -1

    @classmethod
    def meets_condition(cls, data: Namespace) -> bool:
        """
        Check if this command should handle the given arguments
        
        :param data: Command line arguments
        :return: True if this command should handle the arguments
        :rtype: bool
        """
        return hasattr(data, 'command') and data.command == cls._name

    @staticmethod
    def add_options(subparsers) -> None:
        """
        Add command line options for the get_clearpubkey command
        
        :param subparsers: Argument parser subparsers
        """
        clearpubkey_parser = subparsers.add_parser(
            "get_clearpubkey", 
            help="Get clear public key from the card (without PIN or secure channel)"
        )
        
        clearpubkey_parser.add_argument(
            "--key-type", 
            choices=['K1', 'R1'], 
            default='K1',
            help="Key type to use (default: K1)"
        )
        
        clearpubkey_parser.add_argument(
            "--puk", 
            type=str, 
            default='',
            help="PUK code to enable clear pubkey reading capability (required for first use)"
        )
        
        clearpubkey_parser.add_argument(
            "--path", 
            type=str, 
            default='',
            help="BIP path for key derivation (e.g., m/44'/0'/0'). Leave empty for current key."
        )
        
        clearpubkey_parser.add_argument(
            "--compressed", 
            action='store_true',
            default=True,
            help="Return compressed public key format (default: True)"
        )
        
        clearpubkey_parser.add_argument(
            "--uncompressed", 
            action='store_true',
            help="Return uncompressed public key format"
        )
