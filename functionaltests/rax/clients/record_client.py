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
from functionaltests.rax.models.record_model import RecordCallbackModel
from functionaltests.rax.models.record_model import RecordListModel
from functionaltests.rax.models.record_model import RecordModel


class RecordClient(ClassicClientMixin):

    def records_uri(self, domain_id, filters=None):
        path = "/domains/{0}/records".format(domain_id)
        return self.create_uri(path, filters=filters)

    def record_uri(self, domain_id, record_id):
        return "{0}/{1}".format(self.records_uri(domain_id), record_id)

    def list_records(self, domain_id, filters=None, **kwargs):
        url = self.records_uri(domain_id, filters)
        resp, body = self.client.get(url, **kwargs)
        return self.deserialize(resp, body, RecordListModel)

    def get_record(self, domain_id, record_id, **kwargs):
        url = self.record_uri(domain_id, record_id)
        resp, body = self.client.get(url, **kwargs)
        return self.deserialize(resp, body, RecordModel)

    def post_record(self, domain_id, record_model, **kwargs):
        url = self.records_uri(domain_id)
        body = json.dumps({'records': [record_model.to_dict()]})
        resp, body = self.client.post(url, body=body, **kwargs)
        return self.deserialize(resp, body, RecordCallbackModel)

    def put_record(self, domain_id, record_id, record_model, **kwargs):
        url = self.record_uri(domain_id, record_id)
        body = json.dumps({'records': [record_model.to_dict()]})
        resp, body = self.client.put(url, body=body, **kwargs)
        return self.deserialize(resp, body, RecordCallbackModel)

    def delete_record(self, domain_id, record_id, **kwargs):
        url = self.record_uri(domain_id, record_id)
        resp, body = self.client.delete(url, **kwargs)
        return self.deserialize(resp, body, RecordCallbackModel)

    def get_callback_url(self, callback):
        return self._get_callback_url(callback, RecordCallbackModel)

    def wait_for_record(self, callback_model):
        utils.wait_for_condition(lambda: self.is_record_active(callback_model))

    def is_record_active(self, callback_model):
        resp, model = self.get_callback_url(callback_model)
        assert resp.status == 200
        if model.status == "COMPLETED":
            return True
        elif model.status == "ERROR":
            raise Exception("Saw ERROR status")
        return False
