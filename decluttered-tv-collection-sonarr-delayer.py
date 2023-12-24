import os.path
from subprocess import Popen, PIPE
from configparser import ConfigParser
from time import sleep
from win32event import CreateMutex
from win32api import GetLastError
from winerror import ERROR_ALREADY_EXISTS

dir_path = os.path.dirname(os.path.realpath(__file__))
config_filepath = dir_path+"/config.ini"
exists = os.path.exists(config_filepath)
config = None
if exists:
    print("--------config.ini file found at ", config_filepath)
    config = ConfigParser()
    config.read(config_filepath)
else:
    print("---------config.ini file NOT FOUND at ", config_filepath)
    exit(0)

configData = config["SONARR"]

runDelayInSeconds = int(config["SONARR"]["runDelayInSeconds"])
maxInstanceCount = int(config["SONARR"]["maxInstanceCount"])
debugging = config["CONFIG"].getboolean('debugging')

def DelayScriptAndDetermineIfLatestInstance():
    scriptName = 'decluttered-tv-collections.py'

    thisHandle = None

    for handleCount in range(maxInstanceCount):
        thisHandle = CreateMutex(None, 1, scriptName + str(handleCount))
        if GetLastError(  ) == ERROR_ALREADY_EXISTS:
            if handleCount == maxInstanceCount - 1: # all handles taken, just exit
                exit(0)
            continue;
        
        if debugging:
            for interval in range(runDelayInSeconds):
                sleep(1)
                print('Running in ' + str(runDelayInSeconds - interval))
        else: sleep(runDelayInSeconds)

        nextInstanceNum = handleCount + 1
        if nextInstanceNum >= maxInstanceCount: nextInstanceNum = 0

        nextHandleExists = CreateMutex(None, 1, scriptName + str(nextInstanceNum))
    
        if GetLastError(  ) == ERROR_ALREADY_EXISTS:
            if debugging: print("the next higher instance exists, so i exit")
            exit(0)
        else:
            if debugging: print("NO HIGHER instance EXISTS, so i open the script")
            dir_path = os.path.dirname(os.path.realpath(__file__))
            process = Popen(['python.exe', dir_path + '\decluttered-tv-collections.py', '-d'], stdout=PIPE, stderr=PIPE)
            exit(0)

DelayScriptAndDetermineIfLatestInstance()

exit(0)