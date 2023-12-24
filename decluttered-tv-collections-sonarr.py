import asyncio
from sys import exit
from configparser import ConfigParser
import os.path
from plexapi.server import PlexServer
import plexapi.library


dir_path = os.path.dirname(os.path.realpath(__file__))

from subprocess import Popen, PIPE

Popen(['python.exe', '-i', dir_path + '\decluttered-tv-collection-sonarr-delayer.py'], stdout=PIPE, stderr=PIPE)