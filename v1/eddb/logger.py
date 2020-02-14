from logging import getLogger, StreamHandler, DEBUG, INFO, WARNING, ERROR, CRITICAL, basicConfig
from . import settings

class EliteLogger:
    levels = {
        0: DEBUG,
        1: INFO,
        2: WARNING,
        3: ERROR,
        4: CRITICAL
    }

    def __init__(self, name, level=INFO):
        self.logger = getLogger(name)
        format = settings.get('log_format', '%(asctime)-15s %(levelname)s %(name)s: %(message)s')
        basicConfig(format=format)
        for h in self.logger.handlers:
            self.logger.removeHandler(h)
        try:
            self.logger.level = self.levels[level]
        except KeyError:
            self.logger.error('Level unknown. Setting default')
            self.logger.level = INFO
        self.logger.addHandler(StreamHandler())
        self.logger.info(f'Logger starting with level {self.logger.level}')

    def debug(self, *args, **kwargs):
        return self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        return self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        return self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        return self.logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        return self.logger.critical(*args, **kwargs)

if __name__ == '__main__':
    logger = EliteLogger('tester')
    logger.debug('I am debug')
    logger.info('I am info')
    logger.warning('I am warning')
    logger.error('I am error')
    logger.critical('I am critical')
