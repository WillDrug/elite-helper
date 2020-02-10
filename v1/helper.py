from eddb.loader import EDDBLoader, APIS
el = EDDBLoader()
el.update_db_for_api(APIS.LISTINGS.value)