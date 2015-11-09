# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import time

import eventlet
import dns
import dns.rdataclass
import dns.rdatatype
import dns.exception
import dns.flags
import dns.rcode
import dns.message
import dns.opcode
from oslo_config import cfg
from oslo_log import log as logging

from designate import utils
from designate.mdns import base
from designate.i18n import _LI
from designate.i18n import _LW


try:
    import newrelic
    newrelic_loaded = True
except ImportError:
    newrelic_loaded = False

if newrelic_loaded:
    newrelic.agent.initialize('/etc/newrelic/newrelic.ini')

NEWRELIC_GROUP_NAME = 'Designate mDNS'


dns_query = eventlet.import_patched('dns.query')

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class NotifyEndpoint(base.BaseEndpoint):
    RPC_API_VERSION = '2.0'
    RPC_API_NAMESPACE = 'notify'

    @utils.newrelic(newrelic_loaded, NEWRELIC_GROUP_NAME)
    def notify_zone_changed(self, context, domain, host, port, timeout,
                            retry_interval, max_retries, delay):
        """
        :param context: The user context.
        :param domain: The designate domain object.  This contains the domain
            name.
        :param host: A notify is sent to this host.
        :param port: A notify is sent to this port.
        :param timeout: The time (in seconds) to wait for a NOTIFY response
            from server.
        :param retry_interval: The time (in seconds) between retries.
        :param max_retries: The maximum number of retries mindns would do for
            sending a NOTIFY message. After this many retries, mindns gives up.
        :param delay: The time to wait before sending the first NOTIFY request.
        :return: a tuple of (response, current_retry) where
            response is the response on success or None on failure.
            current_retry is the current retry number.
            The return value is just used for testing and not by pool manager.
        """
        time.sleep(delay)
        return self._make_and_send_dns_message(
            domain, host, port, timeout, retry_interval, max_retries,
            notify=True)

    @utils.newrelic(newrelic_loaded, NEWRELIC_GROUP_NAME)
    def poll_for_serial_number(self, context, domain, nameserver, timeout,
                               retry_interval, max_retries, delay):
        """
        :param context: The user context.
        :param domain: The designate domain object.  This contains the domain
            name. domain.serial = expected_serial
        :param nameserver: Destination for the poll
        :param timeout: The time (in seconds) to wait for a SOA response from
            nameserver.
        :param retry_interval: The time (in seconds) between retries.
        :param max_retries: The maximum number of retries mindns would do for
            an expected serial number. After this many retries, mindns returns
            an ERROR.
        :param delay: The time to wait before sending the first request.
        :return: The pool manager is informed of the status with update_status.
        """
        (status, actual_serial, retries) = self.get_serial_number(
            context, domain, nameserver.host, nameserver.port, timeout,
            retry_interval, max_retries, delay)
        self.pool_manager_api.update_status(
            context, domain, nameserver, status, actual_serial)

    def get_serial_number(self, context, domain, host, port, timeout,
                          retry_interval, max_retries, delay):
        """
        :param context: The user context.
        :param domain: The designate domain object.  This contains the domain
            name. domain.serial = expected_serial
        :param host: A notify is sent to this host.
        :param port: A notify is sent to this port.
        :param timeout: The time (in seconds) to wait for a SOA response from
            nameserver.
        :param retry_interval: The time (in seconds) between retries.
        :param max_retries: The maximum number of retries mindns would do for
            an expected serial number. After this many retries, mindns returns
            an ERROR.
        :param delay: The time to wait before sending the first request.
        :return: a tuple of (status, actual_serial, retries)
            status is either "SUCCESS" or "ERROR".
            actual_serial is either the serial number returned in the SOA
            message from the nameserver or None.
            retries is the number of retries left.
            The return value is just used for testing and not by pool manager.
            The pool manager is informed of the status with update_status.
        """
        actual_serial = None
        status = 'ERROR'
        retries = max_retries
        time.sleep(delay)
        while (True):
            (response, retry) = self._make_and_send_dns_message(
                domain, host, port, timeout, retry_interval, retries)
            if response and response.rcode() in (
                    dns.rcode.NXDOMAIN, dns.rcode.REFUSED, dns.rcode.SERVFAIL):
                status = 'NO_DOMAIN'
            elif response and len(response.answer) == 1 \
                    and str(response.answer[0].name) == str(domain.name) \
                    and response.answer[0].rdclass == dns.rdataclass.IN \
                    and response.answer[0].rdtype == dns.rdatatype.SOA:
                # parse the SOA response and get the serial number
                rrset = response.answer[0]
                actual_serial = rrset.to_rdataset().items[0].serial

            if actual_serial is None or actual_serial < domain.serial:
                # TODO(vinod): Account for serial number wrap around.
                retries = retries - retry
                LOG.warn(_LW("Got lower serial for '%(zone)s' to '%(host)s:"
                             "%(port)s'. Expected:'%(es)d'. Got:'%(as)s'."
                             "Retries left='%(retries)d'") %
                         {'zone': domain.name, 'host': host,
                          'port': port, 'es': domain.serial,
                          'as': actual_serial, 'retries': retries})
                if retries > 0:
                    # retry again
                    time.sleep(retry_interval)
                    continue
                else:
                    break
            else:
                # Everything looks good at this point. Return SUCCESS.
                status = 'SUCCESS'
                break

        # Return retries for testing purposes.
        return (status, actual_serial, retries)

    def _make_and_send_dns_message(self, domain, host, port, timeout,
                                   retry_interval, max_retries, notify=False):
        """
        :param domain: The designate domain object.  This contains the domain
            name.
        :param host: The destination host for the dns message.
        :param port: The destination port for the dns message.
        :param timeout: The time (in seconds) to wait for a response from
            destination.
        :param retry_interval: The time (in seconds) between retries.
        :param max_retries: The maximum number of retries mindns would do for
            a response. After this many retries, the function returns.
        :param notify: If true, a notify message is constructed else a SOA
            message is constructed.
        :return: a tuple of (response, current_retry) where
            response is the response on success or None on failure.
            current_retry is the current retry number
        """
        dns_message = self._make_dns_message(domain.name, notify=notify)

        retry = 0
        response = None

        while retry < max_retries:
            retry = retry + 1
            LOG.info(_LI("Sending '%(msg)s' for '%(zone)s' to '%(server)s:"
                         "%(port)d'.") %
                     {'msg': 'NOTIFY' if notify else 'SOA',
                      'zone': domain.name, 'server': host,
                      'port': port})
            response = self._send_dns_message(
                dns_message, host, port, timeout)

            if isinstance(response, dns.exception.Timeout):
                LOG.warn(_LW("Got Timeout while trying to send '%(msg)s' for "
                             "'%(zone)s' to '%(server)s:%(port)d'. Timeout="
                             "'%(timeout)d' seconds. Retry='%(retry)d'") %
                         {'msg': 'NOTIFY' if notify else 'SOA',
                          'zone': domain.name, 'server': host,
                          'port': port, 'timeout': timeout,
                          'retry': retry})
                response = None
                # retry sending the message if we get a Timeout.
                time.sleep(retry_interval)
                continue
            elif isinstance(response, dns_query.BadResponse):
                LOG.warn(_LW("Got BadResponse while trying to send '%(msg)s' "
                             "for '%(zone)s' to '%(server)s:%(port)d'. Timeout"
                             "='%(timeout)d' seconds. Retry='%(retry)d'") %
                         {'msg': 'NOTIFY' if notify else 'SOA',
                          'zone': domain.name, 'server': host,
                          'port': port, 'timeout': timeout,
                          'retry': retry})
                response = None
                break
            # Check that we actually got a NOERROR in the rcode and and an
            # authoritative answer
            elif response.rcode() in (dns.rcode.NXDOMAIN, dns.rcode.REFUSED,
                                      dns.rcode.SERVFAIL):
                LOG.info(_LI("%(zone)s not found on %(server)s:%(port)d") %
                         {'zone': domain.name, 'server': host,
                         'port': port})
                break
            elif not (response.flags & dns.flags.AA) or dns.rcode.from_flags(
                    response.flags, response.ednsflags) != dns.rcode.NOERROR:
                LOG.warn(_LW("Failed to get expected response while trying to "
                             "send '%(msg)s' for '%(zone)s' to '%(server)s:"
                             "%(port)d'.\nResponse message:\n%(resp)s\n") %
                         {'msg': 'NOTIFY' if notify else 'SOA',
                          'zone': domain.name, 'server': host,
                          'port': port, 'resp': str(response)})
                response = None
                break
            else:
                break

        return (response, retry)

    def _make_dns_message(self, zone_name, notify=False):
        """
        This constructs a SOA query or a dns NOTIFY message.
        :param zone_name: The zone name for which a SOA/NOTIFY needs to be
            sent.
        :param notify: If true, a notify message is constructed else a SOA
            message is constructed.
        :return: The constructed message.
        """
        dns_message = dns.message.make_query(zone_name, dns.rdatatype.SOA)
        dns_message.flags = 0
        if notify:
            dns_message.set_opcode(dns.opcode.NOTIFY)
            dns_message.flags |= dns.flags.AA
        else:
            # Setting the flags to RD causes BIND9 to respond with a NXDOMAIN.
            dns_message.set_opcode(dns.opcode.QUERY)
            dns_message.flags |= dns.flags.RD

        return dns_message

    def _send_dns_message(self, dns_message, host, port, timeout):
        """
        :param dns_message: The dns message that needs to be sent.
        :param host: The destination ip of dns_message.
        :param port: The destination port of dns_message.
        :param timeout: The timeout in seconds to wait for a response.
        :return: response or dns.exception.Timeout or dns_query.BadResponse
        """
        try:
            if not CONF['service:mdns'].all_tcp:
                response = dns_query.udp(
                    dns_message, host, port=port, timeout=timeout)
            else:
                response = dns_query.tcp(
                    dns_message, host, port=port, timeout=timeout)
            return response
        except dns.exception.Timeout as timeout:
            return timeout
        except dns_query.BadResponse as badResponse:
            return badResponse
