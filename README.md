# Decluttered TV Collections

Before
<picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/CdOsjhb.png">
 <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/CdOsjhb.png">
 <img alt="YOUR-ALT-TEXT" src="https://i.imgur.com/CdOsjhb.png">
</picture>
After
<picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/13PJdgP.png">
 <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/13PJdgP.png">
 <img alt="YOUR-ALT-TEXT" src="https://i.imgur.com/13PJdgP.png">
</picture>

### How does it work?

Essentially it just takes an existing smart collection, detects concurrent episodes and the amount of episodes per series, and formats it into a new one, based on the settings you've chosen.

### Requirements/Limitations

* Windows 10-11? Have to look into Linux compatibility
* python-plexapi 4.15.7+ (installed by requirements.txt)
* Base Smart Collection to pull from and format into a new collection (this must remain on plex, hiding it is fine, as long as it exists)
* If connecting it to Sonarr importing, Sonarr normally waits for the script to finish for each import before moving on to the next. A workaround is included, as well as a single instance check delayer to prevent mass episode importing from spamming.


#### Sonarr connect scripts work like so: 

* Sonarr Connect  ->  
* decluttered-tv-collections.bat  ->  
* decluttered-tv-collections-sonarr.py  ->  
* decluttered-tv-collection-sonarr-delayer.py  ->  
* decluttered-tv-collections.py

This was the only way to circumvent the Sonarr wait.


### How to Use
<details>
  <summary> pip install -r requirements.txt </summary>
</details>

<details>
  <summary>    Create a base smart collection to format episodes from, sorted by your choice, LIMIT this to a number, (I use 150), or the script will take a while (click for example)</summary>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/GzAw2eb.png">
    <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/GzAw2eb.png">
    <img alt="YOUR-ALT-TEXT" src="https://i.imgur.com/GzAw2eb.png">
  </picture>
</details>

<details>
  <summary> Create config.ini matching config.ini.example with your desired settings </summary>
</details>

<details>
  <summary> Run decluttered-tv-collections.py </summary>
</details>

<details>
  <summary>  Optionally connect to Sonarr (using the .bat file if you're on Windows, click for example)</summary>
  <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/qMtU9l6.png">
   <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/qMtU9l6.png">
   <img alt="YOUR-ALT-TEXT" src="https://i.imgur.com/qMtU9l6.png">
  </picture>
</details>

| Config Setting         | How it Works |
|-----------------------:|-----------|
| collectionToFormatFrom | Name of collection to pull from, and format into the new collection, REQUIRED|
| newFormattedCollectionName | Name of collection to create    |
| episodePerSeriesLimit | How many episodes total per series are allowed in the entire collection, backToBackException can override this if enabled    |
| backToBackEpLimit | This many back to back episodes BESIDES the first one, are allowed, so setting to 1 means 2 total episodes can appear back to back    |
| backToBackException | If there's this many additional episodes BESIDES the first episode, we"ll show the episode, so setting to 4 means 5 episodes back to back will show 2 episodes (set this to 0 to disable it)    |
| backToBackShowFirstAndLast | When the backtoback exception applies, show the first episode of the season instead of what should be there    |
| backToBackExceptionOverridesLimit | When the backtoback exception applies, override the per-series limit    |
| alwaysShowLatestEpisodeFirst | This will attempt to show the latest episode of the season in place of whatever episode is actually appearing, unless it's been shown already    |
