# -*- coding: utf-8 -*-
"""
Module containing Windows Hello user key handling.
"""

import sys

if sys.platform.startswith("win"):
    from .hello import Hello  # noqa: F401

    __all__ = ["Hello"]
