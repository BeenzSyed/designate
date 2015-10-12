"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import

import fixtures
from tempest_lib.exceptions import NotFound

from functionaltests.rax import datagen
from functionaltests.rax.clients.domain_client import DomainClient
from functionaltests.rax.clients.record_client import RecordClient


class DomainFixture(fixtures.Fixture):

    def __init__(self, post_model=None, user='default'):
        super(DomainFixture, self).__init__()
        self.post_model = post_model or datagen.random_domain_data()
        self.user = user

    def _setUp(self):
        super(DomainFixture, self)._setUp()
        self._create_domain()

    def _create_domain(self):
        client = DomainClient.as_user(self.user)
        self.post_resp, callback = client.post_domain(self.post_model)
        assert self.post_resp.status == 202
        # we don't know the domain id until the async job completes
        client.wait_for_domain(callback)

        # we need showDetails=True to get at the domain id
        resp, self.callback = client.get_callback_url(callback)
        assert resp.status == 200
        self.domain = self.callback.response.domains[0]
        self.addCleanup(self.cleanup_domain, client, self.domain.id)

    @classmethod
    def cleanup_domain(cls, client, domain_id):
        try:
            client.delete_domain(domain_id)
        except NotFound:
            pass


class RecordFixture(fixtures.Fixture):

    def __init__(self, domain, post_model=None, user='default'):
        super(RecordFixture, self).__init__()
        self.domain = domain
        self.post_model = post_model or datagen.random_a_record(domain.name)
        self.user = user

    def _setUp(self):
        super(RecordFixture, self)._setUp()
        self._create_record()

    def _create_record(self):
        client = RecordClient.as_user(self.user)
        self.post_resp, callback = client.post_record(
            self.domain.id, self.post_model)
        assert self.post_resp.status == 202
        client.wait_for_record(callback)

        resp, self.callback = client.get_callback_url(callback)
        assert resp.status == 200
        self.record = self.callback.response.records[0]
        self.addCleanup(self.cleanup_record, client, self.domain.id,
                        self.record.id)

    @classmethod
    def cleanup_record(cls, client, domain_id, record_id):
        try:
            client.delete_record(domain_id, record_id)
        except NotFound:
            pass
