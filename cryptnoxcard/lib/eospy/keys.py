import hashlib
import os
import re
import struct
import time
from binascii import hexlify, unhexlify

import base58
import ecdsa

from .utils import sha256, ripemd160, str_to_hex, hex_to_int


def check_wif(key):
    if isinstance(key, str):
        try:
            EOSKey(key)
            return True
        except Exception as ex:
            pass
    return False


class EOSKey:
    def __init__(self, private_str=''):
        ''' '''
        if private_str:
            private_key, format, key_type = self._parse_key(private_str)
            self._sk = ecdsa.SigningKey.from_string(unhexlify(private_key), curve=ecdsa.SECP256k1)
        else:
            prng = self._create_entropy()
            self._sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1, entropy=prng)
        self._vk = self._sk.get_verifying_key()

    def __str__(self):
        return self.to_public()

    def _parse_key(self, private_str):
        ''' '''
        match = re.search("^PVT_([A-Za-z0-9]+)_([A-Za-z0-9]+)$", private_str)
        if not match:
            # legacy WIF - format            
            version_key = self._check_decode(private_str, 'sha256x2')
            # ensure first 2 chars == 0x80
            version = int(version_key[0:2], 16)
            if not version == 0x80:
                raise ValueError('Expected version 0x80, instead got {0}', version)
            private_key = version_key[2:]
            key_type = 'K1'
            format = 'WIF'
        else:
            key_type, key_string = match.groups()
            private_key = self._check_decode(key_string, key_type)
            format = 'PVT'
        return private_key, format, key_type

    def _create_entropy(self):
        ''' '''
        ba = bytearray(os.urandom(32))
        seed = sha256(ba)
        return ecdsa.util.PRNG(seed)

    @staticmethod
    def _check_encode(key_buffer, key_type=None):
        '''    '''
        if isinstance(key_buffer, bytes):
            key_buffer = key_buffer.decode()
        check = key_buffer
        if key_type == 'sha256x2':
            first_sha = sha256(unhexlify(check))
            chksum = sha256(unhexlify(first_sha))[:8]
        else:
            if key_type:
                check += hexlify(bytearray(key_type, 'utf-8')).decode()
            chksum = ripemd160(unhexlify(check))[:8]
        return base58.b58encode(unhexlify(key_buffer + chksum))

    @staticmethod
    def _check_decode(key_string, key_type=None):
        '''    '''
        buffer = hexlify(base58.b58decode(key_string)).decode()
        chksum = buffer[-8:]
        key = buffer[:-8]
        if key_type == 'sha256x2':
            # legacy
            first_sha = sha256(unhexlify(key))
            newChk = sha256(unhexlify(first_sha))[:8]
        else:
            check = key
            if key_type:
                check += hexlify(bytearray(key_type, 'utf-8')).decode()
            newChk = ripemd160(unhexlify(check))[:8]
        # print('newChk: '+newChk)
        if chksum != newChk:
            raise ValueError('checksums do not match: {0} != {1}'.format(chksum, newChk))
        return key

    @staticmethod
    def _recover_key(digest, signature, i):
        ''' Recover the public key from the sig
            http://www.secg.org/sec1-v2.pdf
        '''
        curve = ecdsa.SECP256k1.curve
        G = ecdsa.SECP256k1.generator
        order = ecdsa.SECP256k1.order
        yp = (i % 2)
        r, s = ecdsa.util.sigdecode_string(signature, order)
        x = r + (i // 2) * order
        alpha = ((x * x * x) + (curve.a() * x) + curve.b()) % curve.p()
        beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
        y = beta if (beta - yp) % 2 == 0 else curve.p() - beta
        # generate R
        R = ecdsa.ellipticcurve.Point(curve, x, y, order)
        e = ecdsa.util.string_to_number(digest)
        # compute Q
        Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R + (-e % order) * G)
        # verify message
        if not ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1).verify_digest(signature, digest,
                                                                                            sigdecode=ecdsa.util.sigdecode_string):
            return None
        return ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)

    def _recovery_pubkey_param(self, digest, signature):
        ''' Use to derive a number that will allow for the easy recovery
            of the public key from the signature
        '''
        for i in range(0, 4):
            p = self._recover_key(digest, signature, i)
            if p.to_string() == self._vk.to_string():
                return i

    def _compress_pubkey(self):
        ''' '''
        order = self._sk.curve.generator.order()
        p = self._vk.pubkey.point
        x_str = ecdsa.util.number_to_string(p.x(), order)
        hex_data = bytearray(chr(2 + (p.y() & 1)), 'utf-8')
        compressed = hexlify(hex_data + x_str).decode()
        return compressed

    def to_public(self):
        ''' '''
        cmp = self._compress_pubkey()
        return 'EOS' + self._check_encode(cmp).decode()

    def to_wif(self):
        ''' '''
        pri_key = '80' + hexlify(self._sk.to_string()).decode()
        return self._check_encode(pri_key, 'sha256x2').decode()

    def sign(self, digest):
        ''' '''
        cnt = 0
        # convert digest to hex string
        digest = unhexlify(digest)
        while 1:
            cnt += 1
            if not cnt % 10:
                print('Still searching for a signature. Tried {} times.'.format(cnt))
            # get deterministic k
            k = ecdsa.rfc6979.generate_k(self._sk.curve.generator.order(),
                                         self._sk.privkey.secret_multiplier,
                                         hashlib.sha256,
                                         bytearray(sha256(digest + struct.pack('d', time.time())), 'utf-8')
                                         # use time to randomize
                                         )
            # sign the message
            sigder = self._sk.sign_digest(digest, sigencode=ecdsa.util.sigencode_der, k=k)

            # reformat sig
            r, s = ecdsa.util.sigdecode_der(sigder, self._sk.curve.generator.order())
            sig = ecdsa.util.sigencode_string(r, s, self._sk.curve.generator.order())

            # ensure signature is canonical
            if isinstance(sigder[5], int):
                lenR = sigder[3]
            else:
                lenR = str_to_hex(sigder[3])
            if isinstance(sigder[5 + lenR], int):
                lenS = sigder[5 + lenR]
            else:
                lenS = str_to_hex(sigder[5 + lenR])
            if lenR == 32 and lenS == 32:
                # derive recover parameter
                i = self._recovery_pubkey_param(digest, sig)
                # compressed
                i += 4
                # compact
                i += 27
                break
        # pack
        sigstr = struct.pack('<B', i) + sig
        # encode
        return 'SIG_K1_' + self._check_encode(hexlify(sigstr), 'K1').decode()

    def build_signature(self, digest, public_key, signature, key_type):
        if key_type == "R1":
            a, b = -3, 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
            curve = ecdsa.NIST256p.curve
            g = ecdsa.NIST256p.generator
            order = ecdsa.NIST256p.order
        else:
            curve = ecdsa.SECP256k1.curve
            g = ecdsa.SECP256k1.generator
            order = ecdsa.SECP256k1.order
            a, b = 0, 7
        p = curve.p()
        # get the current public key point
        Qx = int(public_key[2:66], 16)
        Qy = int(public_key[66:130], 16)
        Qpub = ecdsa.ellipticcurve.Point(curve, Qx, Qy, order)

        r = int.from_bytes(signature[4:36], 'big')
        s = int.from_bytes(signature[38:70], 'big')
        # beta = sqrt(x^3+a.x+b) = +/- y
        beta = ecdsa.numbertheory.square_root_mod_prime((pow(r, 3, p) + a * r + b) % p, p)
        y = beta if beta % 2 == 0 else p - beta
        R = ecdsa.ellipticcurve.Point(curve, r, y, order)
        # Q public key recovery. If the public key matches : flags i found
        h = ecdsa.util.string_to_number(digest)
        # Q = 1/r * ( s.R - h.G )
        Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R + (order - h) * g)
        i = 31 if Q == Qpub else 32
        # pack
        ib = i.to_bytes(1, byteorder='big')
        rb = r.to_bytes(32, byteorder='big')
        sb = s.to_bytes(32, byteorder='big')
        sigstr = ib + rb + sb
        # encode

        return 'SIG_' + key_type + '_' + self._check_encode(sigstr.hex(), key_type).decode()

    def verify(self, encoded_sig, digest):
        ''' '''
        # remove SIG_ prefix
        encoded_sig = encoded_sig[4:]
        # remove curve prefix
        curvePre = encoded_sig[:3].strip('_')
        if curvePre != 'K1':
            raise TypeError('Unsupported curve prefix {}'.format(curvePre))

        decoded_sig = self._check_decode(encoded_sig[3:], curvePre)
        # first 2 bytes are recover param
        recover_param = hex_to_int(decoded_sig[:2]) - 4 - 27
        # use sig
        sig = decoded_sig[2:]
        # verify sig
        p = self._recover_key(unhexlify(digest), unhexlify(sig), recover_param)
        return p.verify_digest(unhexlify(sig), unhexlify(digest), sigdecode=ecdsa.util.sigdecode_string)
