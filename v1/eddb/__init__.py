import os
dir_path = os.path.dirname(os.path.realpath(__file__))

settings = {
    'engine': os.getenv('ELITE_DB_ENGINE', f'sqlite:///{dir_path}/data/eddb.db'),
    'log_level': int(os.getenv('ELITE_LOG_LEVEL', 1)),
    'cache_time': int(os.getenv('ELITE_CACHE_TIME', 86400)),
    'procnum': int(os.getenv('ELITE_PROCNUM', 8)),
    'chunksize': int(os.getenv('ELITE_CHUNK_SIZE', -1))  # don't use chunks by default
}