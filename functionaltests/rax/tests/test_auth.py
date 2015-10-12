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

from tempest_lib.exceptions import Unauthorized

from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.blacklist_client import BlacklistClient


class TestAuth(DesignateV2Test):

    def test_regular_user_cannot_list_blacklists(self):
        client = BlacklistClient.as_user('default')
        self.assertRaises(Unauthorized, client.list_blacklists)
