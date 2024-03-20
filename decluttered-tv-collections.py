from sys import exit
from configparser import ConfigParser
import os.path
from plexapi.server import PlexServer
import logging
from datetime import datetime
from sys import stdout

rfh = logging.handlers.RotatingFileHandler(
    filename='decluttered-tv-collections.log', 
    mode='a',
    maxBytes=5*1024*1024,
    backupCount=2,
    encoding='utf8',
    delay=False
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%y-%m-%d %H:%M:%S",
    handlers=[
        rfh
    ]
)

logger = logging.getLogger('decluttered-tv-collections')

def Log(logString):
    stdout.buffer.write(logString.encode('utf8'))
    print("")
    logger.info(logString)

nowTime = datetime.now().strftime('%H:%M:%S %m-%d-%Y')
Log("-------- " + str(nowTime) + ' - Starting Decluttered TV Collections')

dir_path = os.path.dirname(os.path.realpath(__file__))
config_filepath = dir_path+"/config.ini"
exists = os.path.exists(config_filepath)
config = None
if exists:
    Log("config.ini file found at " + config_filepath)
    config = ConfigParser()
    config.read(config_filepath)
else:
    Log("config.ini file NOT FOUND at " + config_filepath)
    exit(0)

configData = config["CONFIG"]

debugging = configData.getboolean('debugging')
testOpenCalc = configData.getboolean('testOpenCalc')
plexHost = configData['plexHost']
plexToken = configData['plexToken']
plexLibraryName = configData['plexLibraryName']

newFormattedCollectionName = configData["newFormattedCollectionName"]
collectionToFormatName = configData["collectionToFormatFrom"]

episodePerSeriesLimit = int(configData["episodePerSeriesLimit"])
backToBackEpLimit = int(configData["backToBackEpLimit"])
backToBackException = int(configData["backToBackException"])
backToBackShowFirstAndLast = configData.getboolean('backToBackShowFirstAndLast')

libraryRecommended = configData.getboolean('libraryRecommended') 
showOnHome = configData.getboolean('showOnHome')
friendsHome = configData.getboolean('friendsHome')
backToBackExceptionOverridesLimit = configData.getboolean('backToBackExceptionOverridesLimit')
alwaysShowLatestEpisodeFirst = configData.getboolean('alwaysShowLatestEpisodeFirst')


plexServer = PlexServer(plexHost, plexToken)
tvLibrary = plexServer.library.section(plexLibraryName)
collectionToFormatFrom = None
formattedNewCollection = None



def Main():
    global collectionToFormatFrom, formattedNewCollection, formattedItemsForCollection

    collectionToFormatFrom, formattedNewCollection = SearchForExistingCollections(collectionToFormatFrom, formattedNewCollection)
    formattedItemsForCollection = FormatFoundCollectionBaseIntoList()

    if not formattedNewCollection:
        formattedNewCollection = CreateNewFormattedCollection(plexServer, collectionToFormatFrom, formattedNewCollection, formattedItemsForCollection)
    else:
        formattedNewCollection = UpdateExistingFormattedCollection(formattedNewCollection, formattedItemsForCollection)

    formattedNewCollection.visibility().updateVisibility(recommended=False, home=False, shared=False)
    SortFormattedCollection(formattedNewCollection, formattedItemsForCollection)
    formattedNewCollection.visibility().updateVisibility(recommended=libraryRecommended, home=showOnHome, shared=friendsHome)

    if debugging: Log("Finished")
    exit(0)




def SearchForExistingCollections(collectionToFormatFrom, formattedNewCollection):
    if debugging: Log('Searching For Existing Collections')
    tvCollectionSearch = tvLibrary.collections(title=newFormattedCollectionName)

    foundCollection = None
    tagToFind = newFormattedCollectionName + ' declut'

    for collection in tvCollectionSearch:
        for label in collection.labels:
            if label.tag == tagToFind:
                if not foundCollection: 
                    foundCollection = collection
                else:
                    if collection != foundCollection:
                        collection.delete()
                        if debugging: Log('  Deleted duplicate collection')

    formattedNewCollection = foundCollection
    collectionToFormatFrom = tvLibrary.collection(title=collectionToFormatName)

    if collectionToFormatFrom: Log('  Base Smart Collection Found: ' + collectionToFormatFrom.title)
    else:
        Log("Base Smart Collection to Format From Not Found, You must create a smart collection on Plex to format from, and place its name in the config")
        exit(0)

    if formattedNewCollection: Log('  Decluttered Collection Found, updating: ' + formattedNewCollection.title)

    return collectionToFormatFrom, formattedNewCollection

def FormatFoundCollectionBaseIntoList():
    if debugging: 
        Log('Formatting Found Collection Base "' + collectionToFormatFrom.title + '" Into List')
        Log('  Adding the following entries to list:')
    seriesShownAlreadyCount = {}
    epsShownAlready = {}
    prevEpShowKey = ""
    backToBackEpCount = 0
    itemsForNewCollection = []
    
    for curVid in collectionToFormatFrom:
        season = curVid.season()
        showKey = curVid.show().key
        epToAppearInColl = None
        isBackToBackException = False

        if showKey not in seriesShownAlreadyCount: seriesShownAlreadyCount[showKey] = 0
    
        seriesEpCount = seriesShownAlreadyCount[showKey] + 1
        if prevEpShowKey == showKey: backToBackEpCount += 1
        else: backToBackEpCount = 0

        if backToBackException != 0 and backToBackEpCount == backToBackException:
            isBackToBackException = True

        if not isBackToBackException or not backToBackExceptionOverridesLimit:
            if seriesEpCount > episodePerSeriesLimit: continue
            if backToBackEpCount > backToBackEpLimit: continue

        
        if isBackToBackException and backToBackShowFirstAndLast:
            epToAppearInColl = season.episodes()[0] #try first episode for back to back
        else: 
            if alwaysShowLatestEpisodeFirst:
                epToAppearInColl = season.episodes()[-1] #try latest episode
            # epToAppearInColl is None if not backToBack and alwaysShowLatest is false

        if epToAppearInColl == None or epToAppearInColl.key in epsShownAlready:
            epToAppearInColl = curVid #try current episode
            
        if epToAppearInColl.key in epsShownAlready: continue # can't display an episode, continue
        
        if debugging: Log('    "' + season.show().title + ' - ' + epToAppearInColl.title + '"')

        itemsForNewCollection.append(epToAppearInColl)
        prevEpShowKey = showKey
        epsShownAlready[epToAppearInColl.key] = True
        seriesShownAlreadyCount[showKey] += 1
    return itemsForNewCollection

def CreateNewFormattedCollection(plex, collectionToFormatFrom, formattedNewCollection, itemsForNewCollection):
    if debugging: Log('Creating New Formatted Collection "' + newFormattedCollectionName + '"')

    formattedNewCollection = collectionToFormatFrom.create(plex, newFormattedCollectionName, 'TV Shows', items=itemsForNewCollection, smart=False, limit=None, libtype=None, sort=None, filters=None)
    formattedNewCollection.sortUpdate(sort="custom")
    formattedNewCollection.modeUpdate(mode="hide")
    formattedNewCollection.addLabel(newFormattedCollectionName + ' declut')
    formattedNewCollection.editSortTitle('  ' + newFormattedCollectionName)
    return formattedNewCollection

def UpdateExistingFormattedCollection(formattedNewCollection, itemsForNewCollection):
    if debugging: Log('Updating Existing Formatted Collection "' + formattedNewCollection.title + '" With New List')
    tvLibrary.batchMultiEdits(formattedNewCollection.items())

    tvLibrary.removeCollection(newFormattedCollectionName)
    tvLibrary.saveMultiEdits()

    tvLibrary.batchMultiEdits(itemsForNewCollection)
    tvLibrary.addCollection(newFormattedCollectionName)
    tvLibrary.saveMultiEdits()

    return formattedNewCollection

def SortFormattedCollection(formattedNewCollection, itemsForNewCollection):
    if debugging: Log('Sorting Formatted Collection On Plex')

    lastEpSorted = None
    for episode in itemsForNewCollection:
        if not lastEpSorted: 
            lastEpSorted = episode 
            continue
        formattedNewCollection.moveItem(episode, after=lastEpSorted)
        lastEpSorted = episode


    

Main()