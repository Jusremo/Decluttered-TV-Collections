import os.path
from subprocess import Popen, PIPE

dir_path = os.path.dirname(os.path.realpath(__file__))
process = Popen(['python.exe', dir_path + '\decluttered-tv-collections.py', '-d'], stdout=PIPE, stderr=PIPE)