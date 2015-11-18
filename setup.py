#!/usr/bin/env python3

from distutils.core import setup, Extension

fasthash = Extension(
        'fasthash',
        sources = ['fasthash.c'],
        libraries = [],
        extra_compile_args = ['-Wall'],
        extra_link_args = [])

setup(
        name = 'Fast hashing',
        ext_modules = [fasthash])

