import os
dir_path = os.path.dirname(os.path.realpath(__file__))

settings = {
    'engine': os.getenv('ELITE_DB_ENGINE', f'sqlite:///{dir_path}/data/eddb.db'),
    'log_level': int(os.getenv('ELITE_LOG_LEVEL', 1)),
    'cache_time': 86400,
    'procnum': int(os.getenv('PROCNUM', 8)),
    'commit_rate': int(os.getenv('COMMIT_RATE', 500))
}