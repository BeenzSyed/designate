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

from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.rax.clients.domain_client import DomainClient
from functionaltests.rax.fixtures import DomainFixture
from functionaltests.rax.fixtures import RecordFixture


class TestSanity(DesignateV2Test):

    def setUp(self):
        super(TestSanity, self).setUp()
        self.classic_client = DomainClient.as_user('default')

    def test_v1_list_domains_sanity_check(self):
        resp, model = self.classic_client.list_domains()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.domains), -1)

    def test_v1_create_domain_sanity_check(self):
        fixture = self.useFixture(DomainFixture())
        self.assertEqual(fixture.post_resp.status, 202)

    def test_v1_create_record_sanity_check(self):
        domain_fixture = self.useFixture(DomainFixture())
        fixture = self.useFixture(RecordFixture(domain_fixture.domain))
        self.assertEqual(fixture.post_resp.status, 202)
