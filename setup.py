#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os,glob
from setuptools import setup, find_packages


setup(
    name = 'qcon',
    version = '2.1',
    scripts=['qcon.py'],

    author = 'pawnhearts',
    author_email = 'ph@kotchan.org',
    description = """qcon is program for hiding/showing terminal emulators(or other software) with a hotkey.""",
    long_description = """qcon is program for hiding/showing terminal emulators(or other software) with a hotkey.
Similar to consoles you see in many FPS games.
Unlike similar projects like guake/yakuake you can use any terminal emulator of your choice.
Several terminals(or other software) can be configured.
It's compact and consists of a single file.""",
    classifiers=[
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Terminals :: Terminal Emulators/X Terminals',
    ],

    license = "MIT",
    url = 'https://github.com/pawnhearts/qcon',
    download_url = 'https://github.com/pawnhearts/qcon/archive/master.zip',
    keywords = "terminal gtk",
    platforms = "POSIX",
    maintainer = 'pawnhearts',
    maintainer_email = 'ph@kotchan.org',
)
