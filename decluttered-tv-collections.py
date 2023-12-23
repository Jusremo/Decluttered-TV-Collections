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

# print(database_config["host"])

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
    lastEpisodeKey = ""
    backToBackEpCount = 0
    itemsForNewCollection = []

    for curVid in collectionToFormatFrom:
        season = curVid.season()
        key = curVid.show().key
        epToAppearInColl = None

        if key not in seriesShownAlreadyCount: seriesShownAlreadyCount[key] = 0
    
        epCount = seriesShownAlreadyCount[key] + 1
        if lastEpisodeKey == key: backToBackEpCount += 1
        else: backToBackEpCount = 0

        if backToBackEpCount != backToBackException and backToBackException != 0:
            if epCount > episodePerSeriesLimit: continue
            if backToBackEpCount > backToBackEpLimit: continue

        if backToBackEpCount == backToBackException and backToBackException != 0:
            if backToBackShowFirstAndLast:
                epToAppearInColl = season.episodes()[0] #try first episode
            else: epToAppearInColl = curVid #try this episode

        else: epToAppearInColl = season.episodes()[-1] #try latest episode

        if epToAppearInColl.key in epsShownAlready:
            if epToAppearInColl.key in epsShownAlready:
                epToAppearInColl = curVid #try this episode
                if epToAppearInColl.key in epsShownAlready:
                    continue #failure, show nothing
            
        if epToAppearInColl.key in epsShownAlready: continue
        
        if debugging: print(season.show().title + ' ' + epToAppearInColl.title)

        itemsForNewCollection.append(epToAppearInColl)
        lastEpisodeKey = key
        epsShownAlready[epToAppearInColl.key] = True
        seriesShownAlreadyCount[key] += 1
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