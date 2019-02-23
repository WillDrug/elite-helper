# Credits right away
EDTS is forked from https://bitbucket.org/Esvandiary/edts/overview

# elite-helper
Helper App for Elite Dangerous, not trying to create another database, but a personal logbook

???!!! what to do what to do

# TODO
1) A package for each object (system, star, planet, etc.)
2) Log parser
3) EDDB\EDDN connection, etc
4) interface up after the initial release
5) do more DRY 
6) microservice up and cache data into DB with async updates
7) do profit reports after trader has concluded
8) create exploration helper
9) create 

# Structure
* **helper.py**: Starts up telegram bot to get commands and such
* **eddb**: Connects and parses EDDB
* **eddi**: Connects to voiceoutput of specially configured EDDI
* **rares**: weird graph-based classes to track buying and selling rare goods and also making money with each trip
* **edts**: what?
* **bot**: contains the afformentioned telgram bot


# Notes
* File location: `%UserProfile%\Saved Games\Frontier Developments\Elite Dangerous`
* Header format `{ "timestamp":"2016-07-22T10:20:01Z", "event":"fileheader", "part":1, "language":"French/FR", "gameversion":"2.2 Beta 1", "build":"r114123 " }`


