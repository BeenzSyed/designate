# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import random
# from mock import patch
from moniker.openstack.common import log as logging
from moniker.tests.test_central import CentralTestCase
from moniker import exceptions

LOG = logging.getLogger(__name__)


class CentralServiceTest(CentralTestCase):
    __test__ = True

    def setUp(self):
        super(CentralServiceTest, self).setUp()
        self.central_service = self.get_central_service()

    def test_start_and_stop(self):
        # Ensures the start/stop actions don't raise
        self.central_service.start()
        self.central_service.stop()

    def test_check_domain_name_blacklist(self):
        self.config(domain_name_blacklist=['^example.org.$', 'net.$'],
                    group='service:central')

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        context = self.get_context()

        self.central_service._check_domain_name_blacklist(context, 'org.')

        self.central_service._check_domain_name_blacklist(
            context, 'www.example.org.')

        with self.assertRaises(exceptions.Forbidden):
            self.central_service._check_domain_name_blacklist(
                context, 'example.org.')

        with self.assertRaises(exceptions.Forbidden):
            self.central_service._check_domain_name_blacklist(
                context, 'example.net.')

    # Server Tests
    def test_create_server(self):
        context = self.get_admin_context()

        values = dict(
            name='ns1.example.org.',
            ipv4='192.0.2.1',
            ipv6='2001:db8::1',
        )

        # Create a server
        server = self.central_service.create_server(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(server['id'])
        self.assertEqual(server['name'], values['name'])
        self.assertEqual(server['ipv4'], values['ipv4'])
        self.assertEqual(server['ipv6'], values['ipv6'])

    def test_get_servers(self):
        context = self.get_admin_context()

        # Ensure we have no servers to start with.
        servers = self.central_service.get_servers(context)
        self.assertEqual(len(servers), 0)

        # Create a single server (using default values)
        self.create_server()

        # Ensure we can retrieve the newly created server
        servers = self.central_service.get_servers(context)
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]['name'], 'ns1.example.org.')

        # Create a second server
        self.create_server(name='ns2.example.org.', ipv4='192.0.2.2',
                           ipv6='2001:db8::2')

        # Ensure we can retrieve both servers
        servers = self.central_service.get_servers(context)
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0]['name'], 'ns1.example.org.')
        self.assertEqual(servers[1]['name'], 'ns2.example.org.')

    def test_get_server(self):
        context = self.get_admin_context()

        # Create a server
        server_name = 'ns%d.example.org.' % random.randint(10, 1000)
        expected_server = self.create_server(name=server_name)

        # Retrieve it, and ensure it's the same
        server = self.central_service.get_server(context,
                                                 expected_server['id'])
        self.assertEqual(server['id'], expected_server['id'])
        self.assertEqual(server['name'], expected_server['name'])
        self.assertEqual(server['ipv4'], expected_server['ipv4'])
        self.assertEqual(server['ipv6'], expected_server['ipv6'])

    def test_update_server(self):
        context = self.get_admin_context()

        # Create a server
        expected_server = self.create_server()

        # Update the server
        values = dict(ipv4='127.0.0.1')
        self.central_service.update_server(context, expected_server['id'],
                                           values=values)

        # Fetch the server again
        server = self.central_service.get_server(context,
                                                 expected_server['id'])

        # Ensure the server was updated correctly
        self.assertEqual(server['ipv4'], '127.0.0.1')

    def test_delete_server(self):
        context = self.get_admin_context()

        # Create a server
        server = self.create_server()

        # Delete the server
        self.central_service.delete_server(context, server['id'])

        # Fetch the server again, ensuring an exception is raised
        with self.assertRaises(exceptions.ServerNotFound):
            self.central_service.get_server(context, server['id'])

    # Domain Tests
    def test_create_domain(self):
        # Create a server
        self.create_server()

        context = self.get_admin_context()

        values = dict(
            name='example.com.',
            email='info@example.com'
        )

        # Create a domain
        domain = self.central_service.create_domain(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])

    def test_create_blacklisted_domain_success(self):
        self.config(domain_name_blacklist=['^blacklisted.com.$'],
                    group='service:central')

        # Set the policy to accept the authz
        self.policy({'use_blacklisted_domain': '@'})

        # Create a server
        self.create_server()

        context = self.get_admin_context()

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        # Create a domain
        domain = self.central_service.create_domain(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])

    def test_create_blacklisted_domain_fail(self):
        self.config(domain_name_blacklist=['^blacklisted.com.$'],
                    group='service:central')

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        context = self.get_admin_context()

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        with self.assertRaises(exceptions.Forbidden):
            # Create a domain
            self.central_service.create_domain(context, values=values)

    def test_get_domains(self):
        context = self.get_admin_context()

        # Ensure we have no domains to start with.
        domains = self.central_service.get_domains(context)
        self.assertEqual(len(domains), 0)

        # Create a single domain (using default values)
        self.create_domain()

        # Ensure we can retrieve the newly created domain
        domains = self.central_service.get_domains(context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], 'example.com.')

        # Create a second domain
        self.create_domain(name='example.net.')

        # Ensure we can retrieve both domain
        domains = self.central_service.get_domains(context)
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['name'], 'example.com.')
        self.assertEqual(domains[1]['name'], 'example.net.')

    def test_get_domain(self):
        context = self.get_admin_context()

        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])
        self.assertEqual(domain['id'], expected_domain['id'])
        self.assertEqual(domain['name'], expected_domain['name'])
        self.assertEqual(domain['email'], expected_domain['email'])

    def test_update_domain(self):
        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Update the domain
        values = dict(email='new@example.com')
        self.central_service.update_domain(context, expected_domain['id'],
                                           values=values)

        # Fetch the domain again
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])

        # Ensure the domain was updated correctly
        self.assertEqual(domain['email'], 'new@example.com')

    def test_update_blacklisted_domain_success(self):
        self.config(domain_name_blacklist=['^blacklisted.com.$'],
                    group='service:central')

        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Set the policy to accept the authz
        self.policy({'use_blacklisted_domain': '@'})

        # Update the domain
        values = dict(name='blacklisted.com.')
        self.central_service.update_domain(context, expected_domain['id'],
                                           values=values)

        # Fetch the domain again
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])

        # Ensure the domain was updated correctly
        self.assertEqual(domain['name'], 'blacklisted.com.')

    def test_update_blacklisted_domain_fail(self):
        self.config(domain_name_blacklist=['^blacklisted.com.$'],
                    group='service:central')

        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        # Update the domain
        with self.assertRaises(exceptions.Forbidden):
            values = dict(name='blacklisted.com.')
            self.central_service.update_domain(context, expected_domain['id'],
                                               values=values)

    def test_delete_domain(self):
        context = self.get_admin_context()

        # Create a domain
        domain = self.create_domain()

        # Delete the domain
        self.central_service.delete_domain(context, domain['id'])

        # Fetch the domain again, ensuring an exception is raised
        with self.assertRaises(exceptions.DomainNotFound):
            self.central_service.get_domain(context, domain['id'])

    # Record Tests
    def test_create_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='www.example.com.',
            type='A',
            data='127.0.0.1'
        )

        # Create a record
        record = self.central_service.create_record(context, domain['id'],
                                                    values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertIsNone(record['ttl'])
        self.assertEqual(record['name'], values['name'])
        self.assertEqual(record['type'], values['type'])
        self.assertEqual(record['data'], values['data'])

    def test_get_records(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Ensure we have no records to start with.
        records = self.central_service.get_records(context, domain['id'])
        self.assertEqual(len(records), 0)

        # Create a single record (using default values)
        self.create_record(domain)

        # Ensure we can retrieve the newly created record
        records = self.central_service.get_records(context, domain['id'])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['name'], 'www.example.com.')

        # Create a second record
        self.create_record(domain, name='mail.example.com.')

        # Ensure we can retrieve both records
        records = self.central_service.get_records(context, domain['id'])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['name'], 'www.example.com.')
        self.assertEqual(records[1]['name'], 'mail.example.com.')

    def test_get_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        record_name = '%d.example.com' % random.randint(10, 1000)
        expected_record = self.create_record(domain, name=record_name)

        # Retrieve it, and ensure it's the same
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])
        self.assertEqual(record['id'], expected_record['id'])
        self.assertEqual(record['name'], expected_record['name'])

    def test_update_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        expected_record = self.create_record(domain)

        # Update the server
        values = dict(data='127.0.0.2')
        self.central_service.update_record(context, domain['id'],
                                           expected_record['id'],
                                           values=values)

        # Fetch the record again
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], '127.0.0.2')

    def test_delete_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        record = self.create_record(domain)

        # Delete the record
        self.central_service.delete_record(context, domain['id'], record['id'])

        # Fetch the record again, ensuring an exception is raised
        with self.assertRaises(exceptions.RecordNotFound):
            self.central_service.get_record(context, domain['id'],
                                            record['id'])
