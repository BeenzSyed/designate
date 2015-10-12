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

from tempest_lib.exceptions import Conflict


from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.common import datagen as v2_datagen
from functionaltests.rax import datagen as classic_datagen
from functionaltests.rax.fixtures import DomainFixture
from functionaltests.rax.clients.domain_client import DomainClient

from functionaltests.common.utils import parameterized_class
from functionaltests.common.utils import parameterized


DATASET = {
    'conflicting_subsubsub_domain':
        dict(create_prefix='a.b.c.', attempt_prefix=''),
    'conflicting_subsub_domain':
        dict(create_prefix='a.b.', attempt_prefix=''),
    'conflicting_sub_domain':
        dict(create_prefix='a.', attempt_prefix=''),
    'duplicate_domain':
        dict(create_prefix='', attempt_prefix=''),
    'conflicting_super_domain':
        dict(create_prefix='a.b.c.', attempt_prefix='b.c.'),
    'conflicting_supersuper_domain':
        dict(create_prefix='a.b.c.', attempt_prefix='c.'),
    'conflicting_sibling_domain':
        dict(create_prefix='a.', attempt_prefix='b.'),
}


@parameterized_class
class TestPanama(DesignateV2Test):

    def setUp(self):
        super(TestPanama, self).setUp()
        self.classic_model = classic_datagen.random_domain_data()
        self.v2_model = v2_datagen.random_zone_data(
            name=self.classic_model.name + '.')

        # domain is v1/classic; zone is v2/designate
        self.domain_client = DomainClient.as_user('default')
        self.zone_client = ZoneClient.as_user('default')

    @parameterized(DATASET)
    def test_classic_cannot_create_a(self, create_prefix, attempt_prefix):
        """Check that Classic is checking Panama for duplicates."""
        self.v2_model.name = create_prefix + self.v2_model.name
        self.classic_model.name = attempt_prefix + self.classic_model.name

        self.useFixture(ZoneFixture(self.v2_model))

        resp, callback = self.domain_client.post_domain(self.classic_model)
        self.assertEqual(resp.status, 202)
        self.assertRaises(
            Exception, self.domain_client.wait_for_domain, callback)

    @parameterized(DATASET)
    def test_designate_cannot_create_a(self, create_prefix, attempt_prefix):
        self.classic_model.name = create_prefix + self.classic_model.name
        self.v2_model.name = attempt_prefix + self.v2_model.name

        self.useFixture(DomainFixture(self.classic_model))

        self.assertRaises(Conflict, self.zone_client.post_zone, self.v2_model)
