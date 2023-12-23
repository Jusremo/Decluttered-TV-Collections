from sys import exit
from configparser import ConfigParser
import os.path
from plexapi.server import PlexServer
import plexapi.library


dir_path = os.path.dirname(os.path.realpath(__file__))
config_filepath = dir_path+"/config.ini"
exists = os.path.exists(config_filepath)
config = None
if exists:
    print("--------config.ini file found at ", config_filepath)
    config = ConfigParser()
    config.read(config_filepath)
else:
    print("---------config.ini file not found at ", config_filepath)


configData = config["CONFIG"]

debugging = configData.getboolean('debugging')
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
        formattedNewCollection = UpdateFormattedCollection(formattedNewCollection, formattedItemsForCollection)

    formattedNewCollection.visibility().updateVisibility(recommended=False, home=False, shared=False)
    SortFormattedCollection(formattedNewCollection, formattedItemsForCollection)
    formattedNewCollection.visibility().updateVisibility(recommended=libraryRecommended, home=showOnHome, shared=friendsHome)

    if debugging: print("Finished")
    exit(0)



def SearchForExistingCollections(collectionToFormatFrom, formattedNewCollection):
    tvCollectionSearch = tvLibrary.collections(title=newFormattedCollectionName)

    for collection in tvCollectionSearch:
        for label in collection.labels:
            if label.tag == newFormattedCollectionName:
                formattedNewCollection = collection

    collectionToFormatFrom = tvLibrary.collection(title=collectionToFormatName)

    if debugging:
        print('collectionToFormatFrom: ' + collectionToFormatFrom.title)
        print('formattedNewCollection: ' + formattedNewCollection.title)

    return collectionToFormatFrom, formattedNewCollection

def FormatFoundCollectionBaseIntoList():
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
        
        if debugging: print(season.show().title + ' ' + epToAppearInColl.title)

        itemsForNewCollection.append(epToAppearInColl)
        prevEpShowKey = showKey
        epsShownAlready[epToAppearInColl.key] = True
        seriesShownAlreadyCount[showKey] += 1
    return itemsForNewCollection

def CreateNewFormattedCollection(plex, collectionToFormatFrom, formattedNewCollection, itemsForNewCollection):
    formattedNewCollection = collectionToFormatFrom.create(plex, newFormattedCollectionName, 'TV Shows', items=itemsForNewCollection, smart=False, limit=None, libtype=None, sort=None, filters=None)
    formattedNewCollection.sortUpdate(sort="custom")
    formattedNewCollection.modeUpdate(mode="hide")
    formattedNewCollection.addLabel(newFormattedCollectionName)
    formattedNewCollection.editSortTitle('  ' + newFormattedCollectionName)
    return formattedNewCollection

def UpdateFormattedCollection(formattedNewCollection, itemsForNewCollection):
    tvLibrary.batchMultiEdits(formattedNewCollection.items())
    tvLibrary.removeCollection(newFormattedCollectionName)
    tvLibrary.saveMultiEdits()

    tvLibrary.batchMultiEdits(itemsForNewCollection)
    tvLibrary.addCollection(newFormattedCollectionName)
    tvLibrary.saveMultiEdits()

    return formattedNewCollection

def SortFormattedCollection(formattedNewCollection, itemsForNewCollection):
    lastEpSorted = None
    for episode in itemsForNewCollection:
        if not lastEpSorted: 
            lastEpSorted = episode 
            continue
        formattedNewCollection.moveItem(episode, after=lastEpSorted)
        lastEpSorted = episode


Main()