# Copyright (c) 2011-2016 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import datetime
from collections import defaultdict

from lunr.common.config import LunrConfig
from lunr.db.models import Error, Event, Marker
from lunr import db
import lunr.orbit.jobs.purge_accounts
from lunr.orbit.jobs.purge_accounts import PurgeAccounts
from testlunr.unit import patch


class MockLog(object):
    msg = ""

    def info(self, msg):
        self.msg = msg

    def error(self, msg):
        self.msg = msg


class TestPurgeAccounts(unittest.TestCase):
    def setUp(self):
        self.conf = LunrConfig({'db': {'auto_create': True,
                                       'url': 'sqlite://'}})
        self.sess = db.configure(self.conf)
        self.log = MockLog()
        self.reader = PurgeAccounts(self.conf, self.sess)

    def tearDown(self):
        self.sess.close()

    # def test_run(self):
    #    self.reader.run()

    def test_log_to_db_empty_event(self):
        error_msg = "Test Exception"
        self.reader.log_error_to_db(Exception(error_msg))
        obj = self.sess.query(Error).filter(Error.message == error_msg).first()
        self.assertEqual(obj.message, error_msg)
        self.assertEqual(obj.event_id, None)
        self.assertEqual(obj.tenant_id, None)

    def test_log_to_db_with_event(self):
        error_msg = "Test Exception"
        event = Event(tenant_id='123', id='345')
        self.reader.log_error_to_db(Exception(error_msg), event)
        obj = self.sess.query(Error).filter(Error.message == error_msg).first()
        self.assertEqual(obj.message, error_msg)
        self.assertEqual(obj.tenant_id, event.tenant_id)
        self.assertEqual(obj.event_id, event.event_id)

    def test_remove_errors(self):
        mock_error = Error(event_id="123", tenant_id="456",
                           message=str("Test Exception"), type="test")
        mock_event = Event(event_id="123", tenant_id="456")
        self.sess.add(mock_error)
        self.reader.remove_errors(mock_event, "test")
        obj = self.sess.query(Error).filter(Error.type == "test").first()
        self.assertEqual(obj, None)

    def test_collect_totals(self):
        pass

    def test_fetch_events(self):
        events = self.reader.fetch_events()
        self.assertIsNotNone(events)

    def tests_save_processed_event(self):
        mock_event = Event(event_id='2345',
        tenant_id='1234',
        timestamp= datetime.datetime.utcnow(),
        processed='No',
        last_purged=None)
        self.sess.add(mock_event)
        self.sess.commit()
        self.reader.save_processed_event(mock_event)
        # fetch processed record
        processed_record = self.sess.query(Event).filter(Event.event_id == mock_event.event_id).first()
        self.assertEquals(processed_record.event_id, mock_event.event_id)
        self.assertEquals(processed_record.processed, 'Yes')
        self.assertIsNotNone(processed_record.last_purged)