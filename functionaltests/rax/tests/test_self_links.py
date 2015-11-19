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

from functionaltests.common import datagen
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.clients.zone_import_client import ZoneImportClient
from functionaltests.api.v2.clients.zone_export_client import ZoneExportClient
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.api.v2.fixtures import RecordsetFixture
from functionaltests.api.v2.fixtures import ZoneImportFixture
from functionaltests.api.v2.fixtures import ZoneExportFixture
from functionaltests.rax.config import cfg


class TestSelfLinks(DesignateV2Test):

    def setUp(self):
        super(TestSelfLinks, self).setUp()
        self.increase_quotas(user='default')
        self.zone = self.useFixture(ZoneFixture(user='default')).created_zone

    def test_zone_self_link(self):
        self.assertIn(cfg.CONF.identity.designate_override_url,
                      self.zone.links['self'])
        link = self.zone.links['self']\
            .split(cfg.CONF.identity.designate_override_url)
        resp, body = ZoneClient.as_user('default').client.get(link[1])
        self.assertEqual(200, resp.status)

    def test_recordset_self_link(self):
        post_model = datagen.random_a_recordset(self.zone.name)
        fixture = self.useFixture(RecordsetFixture(self.zone.id, post_model))
        recordset_id = fixture.created_recordset.id

        resp, model = RecordsetClient.as_user('default')\
            .get_recordset(self.zone.id, recordset_id)
        self.assertIn(cfg.CONF.identity.designate_override_url,
                      model.links['self'])
        self_link = model.links['self']\
            .split(cfg.CONF.identity.designate_override_url)
        resp, body = ZoneClient.as_user('default').client.get(self_link[1])
        self.assertEqual(200, resp.status)
        self.assertIn(cfg.CONF.identity.tenant_name, model.links['self'])

    def test_import_domain_self_link(self):
        user = 'default'
        import_client = ZoneImportClient.as_user(user)

        fixture = self.useFixture(ZoneImportFixture(user=user))
        import_id = fixture.zone_import.id

        resp, model = import_client.get_zone_import(import_id)
        self.assertEqual(200, resp.status)
        self.assertEqual('COMPLETE', model.status)

        self.assertIn(cfg.CONF.identity.designate_override_url,
                      model.links['self'])
        self_link = model.links['self']\
            .split(cfg.CONF.identity.designate_override_url)
        resp, body = ZoneClient.as_user('default').client.get(self_link[1])
        self.assertEqual(200, resp.status)
        self.assertIn(cfg.CONF.identity.tenant_name, model.links['zone'])
        self.assertIn(cfg.CONF.identity.tenant_name, model.links['self'])

    def test_export_domain_self_link(self):
        user = 'default'
        zone_fixture = self.useFixture(ZoneFixture(user=user))
        zone = zone_fixture.created_zone

        export_fixture = self.useFixture(ZoneExportFixture(zone.id, user=user))
        export_id = export_fixture.zone_export.id

        export_client = ZoneExportClient.as_user(user)

        resp, model = export_client.get_zone_export(export_id)
        self.assertEqual(200, resp.status)
        self.assertEqual('COMPLETE', model.status)

        self.assertIn(cfg.CONF.identity.designate_override_url,
                      model.links['self'])
        self_link = model.links['self']\
            .split(cfg.CONF.identity.designate_override_url)
        resp, body = ZoneClient.as_user('default').client.get(self_link[1])
        self.assertEqual(200, resp.status)
        self.assertIn(cfg.CONF.identity.tenant_name, model.links['export'])
        self.assertIn(cfg.CONF.identity.tenant_name, model.links['self'])
