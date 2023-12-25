import os.path
from subprocess import Popen, PIPE

dir_path = os.path.dirname(os.path.realpath(__file__))
process = Popen(['python.exe', '-i', dir_path + '\decluttered-tv-collection-sonarr-delayer.py'], stdout=PIPE, stderr=PIPE)