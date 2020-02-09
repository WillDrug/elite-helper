from eddb.loader import EDDBLoader, APIS
el = EDDBLoader()
el.recache(APIS.COMMODITIES.value)