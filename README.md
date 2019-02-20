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

# Structure
* **listener.py**: Starts a loop listening to Elite logs and parsing them to storage
* **\_\_elite\_\_**: Connects to Elite logs, listening for events, later will connect to EDDB\EDMC\etc.
* **\_\_storage\_\_**: Connects to a background running DB, hold ORM classes
* **\_\_??\_\_**


# Notes
* File location: `%UserProfile%\Saved Games\Frontier Developments\Elite Dangerous`
* Header format `{ "timestamp":"2016-07-22T10:20:01Z", "event":"fileheader", "part":1, "language":"French/FR", "gameversion":"2.2 Beta 1", "build":"r114123 " }`


