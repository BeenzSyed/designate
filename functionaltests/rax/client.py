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

import json

from tempest_lib.common.rest_client import ResponseBody
from tempest_lib.common.rest_client import RestClient
from tempest_lib.auth import KeystoneV2Credentials
from tempest_lib.auth import KeystoneV2AuthProvider
from tempest_lib.services.identity.v2.token_client import TokenClient

from functionaltests.common.client import ClientMixin
from functionaltests.common.utils import memoized
from functionaltests.rax.config import cfg


class ApiKeyTokenClient(TokenClient):
    """A client that uses api key auth for rackspace identity instead"""

    PASSWORD_AUTH = 'password'
    API_KEY_AUTH = 'apiKey'

    def __init__(self, auth_method, *args, **kwargs):
        """
        :params auth_method: either 'password' or 'apiKey'
        """
        super(ApiKeyTokenClient, self).__init__(*args, **kwargs)
        self.auth_method = auth_method
        assert self.auth_method in (self.PASSWORD_AUTH, self.API_KEY_AUTH)

    def auth(self, user, password, tenant=None):
        """
        :param password: Pass in the api key here
        :param tenant: This is ignored for api key auth
        """
        if self.auth_method == self.PASSWORD_AUTH:
            creds = self._password_creds(user, password, tenant)
        else:
            assert self.auth_method == self.API_KEY_AUTH
            creds = self._api_key_creds(user, password)
        body = json.dumps(creds)
        resp, body = self.post(self.auth_url, body=body)
        self.expected_success(200, resp.status)
        return ResponseBody(resp, body['access'])

    def auth_token(self, token_client, tenant=None):
        raise NotImplementedError()

    def _api_key_creds(self, user, password):
        return {
            'auth': {
                'apiKeyCredentials': {
                    'username': user,
                    'apiKey': password,
                }
            }
        }

    def _password_creds(user, password, tenant=None):
        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': user,
                    'password': password,
                }
            }
        }
        if tenant:
            creds['auth']['tenantName'] = tenant
        return creds


class IdentityAuthProvider(KeystoneV2AuthProvider):

    def __init__(self, auth_method, *args, **kwargs):
        self.auth_method = auth_method
        super(IdentityAuthProvider, self).__init__(*args, **kwargs)

    def _auth_client(self, auth_url):
        return ApiKeyTokenClient(
            self.auth_method,
            auth_url,
            disable_ssl_certificate_validation=self.dsvm,
            ca_certs=self.ca_certs,
            trace_requests=self.trace_requests)

    def base_url(self, *args, **kwargs):
        if cfg.CONF.rax.endpoint:
            return cfg.CONF.rax.endpoint
        result = super(IdentityAuthProvider, self).base_url(*args, **kwargs)
        return result


class ClassicClient(RestClient):

    def __init__(self):
        super(ClassicClient, self).__init__(
            auth_provider=self._get_auth_provider(),
            service='rax:dns',
            region='DEFAULT',
        )

    def _get_auth_provider(self):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.rax.username,
            password=cfg.CONF.rax.apikey,
            tenant_name=cfg.CONF.rax.tenant_name,
        )
        auth_provider = IdentityAuthProvider(
            ApiKeyTokenClient.API_KEY_AUTH,
            creds,
            cfg.CONF.rax.auth_url,
        )
        auth_provider.fill_credentials()
        return auth_provider


class ClassicClientMixin(ClientMixin):

    @classmethod
    @memoized
    def get_clients(cls, with_token):
        """
        :param with_token: IGNORED
        """
        return {
            'default': ClassicClient(),
        }

    def create_uri(self, path, filters=None):
        if filters:
            return self.add_filters(path, filters)
        return path

    def _get_callback_url(self, callback, returned_model):
        """Don't call directly. This should be called from subclasses that know
        which callback model to deserialize to.
        """
        path = '/status/{0}?showDetails=true'.format(callback.jobId)
        resp, body = self.client.get(path)
        return self.deserialize(resp, body, returned_model)
