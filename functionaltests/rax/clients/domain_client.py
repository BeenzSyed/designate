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

from functionaltests.common import utils
from functionaltests.rax.client import ClassicClientMixin
from functionaltests.rax.models.domain_model import DomainCallbackModel
from functionaltests.rax.models.domain_model import DomainListModel
from functionaltests.rax.models.domain_model import DomainModel


class DomainClient(ClassicClientMixin):

    def domains_uri(self, filters=None):
        return self.create_uri("/domains", filters=filters)

    def domain_uri(self, id):
        return "{0}/{1}".format(self.domains_uri(), id)

    def list_domains(self, filters=None, **kwargs):
        resp, body = self.client.get(self.domains_uri(filters), **kwargs)
        return self.deserialize(resp, body, DomainListModel)

    def get_domain(self, id, **kwargs):
        resp, body = self.client.get(self.domain_uri(id), **kwargs)
        return self.deserialize(resp, body, DomainModel)

    def post_domain(self, domain_model, **kwargs):
        body = json.dumps({'domains': [domain_model.to_dict()]})
        resp, body = self.client.post(self.domains_uri(), body=body, **kwargs)
        return self.deserialize(resp, body, DomainCallbackModel)

    def put_domain(self, id, domain_model, **kwargs):
        resp, body = self.client.put(self.domains_uri(id),
            body=domain_model.to_json(), **kwargs)
        return self.deserialize(resp, body, DomainCallbackModel)

    def delete_domain(self, id, **kwargs):
        resp, body = self.client.delete(self.domain_uri(id), **kwargs)
        return self.deserialize(resp, body, DomainCallbackModel)

    def get_callback_url(self, callback):
        return self._get_callback_url(callback, DomainCallbackModel)

    def wait_for_domain(self, callback_model):
        utils.wait_for_condition(lambda: self.is_domain_active(callback_model))

    def is_domain_active(self, callback_model):
        resp, model = self.get_callback_url(callback_model)
        assert resp.status == 200
        if model.status == "COMPLETED":
            return True
        elif model.status == "ERROR":
            raise Exception("Saw ERROR status")
        return False
