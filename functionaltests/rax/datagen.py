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
import random

from functionaltests.common.datagen import random_ip
from functionaltests.common.datagen import random_string
from functionaltests.rax.models.domain_model import DomainModel
from functionaltests.rax.models.record_model import RecordModel


def random_domain_data(name=None, email=None, ttl=None, comment=None):
    if name is None:
        name = random_string(prefix='testdomain', suffix='.com')
    if email is None:
        email = "admin@{0}".format(name)
    if ttl is None:
        ttl = random.randint(1200, 8400)
    if comment is None:
        comment = random_string(prefix='Comment ')
    return DomainModel.from_dict({
        'name': name,
        'emailAddress': email,
        'ttl': ttl,
        'comment': comment,
    })


def random_record_data(record_type, zone_name, name=None, data=None,
                       ttl=None):
    """Generate random record data, with optional overrides

    :return: A RecordModel
    """
    if name is None:
        name = random_string(prefix=record_type, suffix='.' + zone_name)
    if data is None:
        data = data
    if ttl is None:
        ttl = random.randint(1200, 8400)
    return RecordModel.from_dict({
        'type': record_type,
        'name': name,
        'data': data,
        'ttl': ttl,
    })

def random_a_record(zone_name, ip=None, **kwargs):
    if ip is None:
        ip = random_ip()
    return random_record_data('A', zone_name, data=ip, **kwargs)
