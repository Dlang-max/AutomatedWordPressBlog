"""
A celerybeat scheduler with a Redis backend.
"""

import logging

import six.moves.cPickle as pickle
from six.moves.urllib.parse import urlsplit

from celery.beat import Scheduler
from celery import current_app
import redis


class RedisScheduler(Scheduler):
    def __init__(self, *args, **kwargs):

        # XXX It's ugly to use something called 'filename' as a URI.  Make an
        # upstream ticket for a nicer way of passing config into a custom
        # scheduler backend.
        self.uri = current_app.conf['CELERYBEAT_SCHEDULE_FILENAME']
        logging.debug('RedisScheduler connecting to %s', self.uri)
        self.redis = redis.StrictRedis(**parse_redis_uri(self.uri))

        # XXX Would be nice to make this configurable.
        self.redis_key = 'celerybeat_schedule'

        # If there's not already an 'entries' key, create one.
        pickled = self.redis.get(self.redis_key)
        if not pickled:
            self.entries = {}
            self.sync()
        else:
            self.entries = pickle.loads(pickled)
        super(RedisScheduler, self).__init__(*args, **kwargs)

    def setup_schedule(self):
        self.merge_inplace(self.app.conf.CELERYBEAT_SCHEDULE)
        self.install_default_entries(self.schedule)
        self.sync()

    def get_schedule(self):
        return self.entries

    def set_schedule(self, schedule):
        self.entries = schedule
        self.sync()
    schedule = property(get_schedule, set_schedule)

    def sync(self):
        self.redis.set(self.redis_key, pickle.dumps(self.entries))

    def close(self):
        self.sync()
        self.redis.connection_pool.disconnect()

    @property
    def info(self):
        return self.uri


def parse_redis_uri(uri):
    """
    Given a uri like redis://localhost:6379/0, return a dict with host, port,
    and db members.
    """
    parsed = urlsplit(uri)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'db': int(parsed.path.replace('/', '')),
    }
