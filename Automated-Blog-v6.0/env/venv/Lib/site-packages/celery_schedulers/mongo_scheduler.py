"""
A celerybeat scheduler with a Mongo backend.
"""

import logging

import six.moves.cPickle as pickle

from celery.beat import Scheduler
from celery import current_app
import pymongo


class MongoScheduler(Scheduler):
    def __init__(self, *args, **kwargs):

        # XXX It's ugly to use something called 'filename' as a URI.  Make an
        # upstream ticket for a nicer way of passing config into a custom
        # scheduler backend.
        self.uri = current_app.conf['CELERYBEAT_SCHEDULE_FILENAME']
        logging.debug('MongoScheduler connecting to %s', self.uri)
        parsed = pymongo.uri_parser.parse_uri(self.uri)
        conn = pymongo.Connection(*parsed['nodelist'][0])
        db = conn[parsed['database']]
        self.collection = db[parsed['collection']]

        # No two documents may have the same 'key'
        self.collection.ensure_index('key', unique=True)

        # If there's not already an 'entries' key, create one.
        entries = self.collection.find_one({'key': 'entries'})
        if not entries:
            self.entries = {}
            self.sync()
        else:
            self.entries = pickle.loads(str(entries['entries']))
        super(MongoScheduler, self).__init__(*args, **kwargs)

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
        self.collection.update(
            {'key': 'entries'},
            {'key': 'entries', 'entries':
             pickle.dumps(self.entries)},
            upsert=True)

    def close(self):
        self.sync()
        self.collection.database.connection.close()

    @property
    def info(self):
        return self.uri
