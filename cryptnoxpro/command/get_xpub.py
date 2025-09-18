# -*- coding: utf-8 -*-
"""
Module containing command for getting extended public key (xpub) from the card
"""
import cryptnoxpy
from argparse import Namespace

from .command import Command
from .helper.security import check

try:
    import enums
except ImportError:
    from .. import enums


class getXpub(Command):
    """
    Command to get the extended public key (get_xpub) from the card
    """
    _name = "get_xpub"

    def _execute(self, card) -> int:
        """
        Execute the xpub command to get extended public key from the card
        
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
            
            if key_type == cryptnoxpy.KeyType.R1:
                print("Cannot get extended public key for R1 key.")
            else:
                # For K1 keys, use clear pubkey reading for xpub
                try:
                    print("Getting extended public key for K1 key...")
                    
                    # Enable clear pubkey reading if PUK provided
                    if puk:
                        print("Enabling clear pubkey reading capability...")
                    
                    # Use clear pubkey reading (P1=0x00, P2=0x01)
                    xpubkey = card.get_public_key_extended(key_type=key_type, puk=puk)
                    print(f"\nK1 Extended Public Key")
                    print(f"{xpubkey}")
                    
                except Exception as e:
                    print(f"Error getting K1 public key: {e}")
                    return -1
            
            return 0
            
        except cryptnoxpy.exceptions.SeedException:
            print("Error: No seed exists on the card. Please initialize the card first.")
            return -1
        except cryptnoxpy.exceptions.ReadPublicKeyException as e:
            print(f"Error reading public key: {e}")
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
        Add command line options for the xpub command
        
        :param subparsers: Argument parser subparsers
        """
        xpub_parser = subparsers.add_parser(
            "get_xpub", 
            help="Get public key using clear pubkey reading (P1=0x01) capability"
        )
        
        xpub_parser.add_argument(
            "--key-type", 
            choices=['K1', 'R1'], 
            default='K1',
            help="Key type to use (default: K1). Uses clear pubkey reading for both types."
        )
        
        xpub_parser.add_argument(
            "--puk", 
            type=str, 
            default='',
            help="PUK code to enable clear pubkey reading capability (if required)"
        )
