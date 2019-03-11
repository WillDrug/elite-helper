# Credits right away
EDTS is forked from https://bitbucket.org/Esvandiary/edts/overview

# elite-helper
Helper App for Elite Dangerous, not trying to create another database, but a personal logbook

???!!! what to do what to do

# TODO
1) Get rid of EDDI dependency
2) Create original logbook connection package
3) Move interface from `helper` to a package
4) Create several interface types, including dynamicly generated terminaltables and\or CURSE generated menu
5) Replicate rare goods graph engine for the entire known universe
6) Devise exploration helper
7) Formulate actually useful functions (like, "source", trying to find closest *and* cheapest commodity location)

# Structure
* **helper.py**: Starts up EDDI and command IOLoop, pre-plotting a course through stations who sale rare goods and suggesting X more possible jumps.
**Jump rules**: Away from stations selling rares currently in cargo, without missing the closest station, maximum profit to minimum distance. 
* **eddb**: Connects to, stores and provides readers for EDDB "api"
  * **system**: Filtering function and a class to hold a star system
  * **station**: Filtering function and a class to hold a station
  * **pricelist**: Filtering function and a class to hold price listings
  * **commodity**: Commodity reference to convert names to IDs and back, also check tradeability
  * **multiprocessing_config**: **UNUSED**
  * **progress_tracker**: Now used to just generate progress bars where necessary.
* **eddi**: Connects to voiceoutput of specially configured EDDI.
* **rares**: Loads up and populates systems, stations and prices into a custom-made graph engine. Pre-generates a route through a return algorythm, trying to find a profitable loop. Can also generate a profitable-next-jump, but only through stations which sell rare goods.
**Upon init** will filter and find the current station and use that to propose the next jump and find the first node to plot from. 
* **edts**: Tools not used in automated code, cloned (look above)
* **sell_the_world**: Empty for now.


# Notes
* File location: `%UserProfile%\Saved Games\Frontier Developments\Elite Dangerous`
* Header format `{ "timestamp":"2016-07-22T10:20:01Z", "event":"fileheader", "part":1, "language":"French/FR", "gameversion":"2.2 Beta 1", "build":"r114123 " }`
