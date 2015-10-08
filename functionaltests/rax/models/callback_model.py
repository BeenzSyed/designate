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

from functionaltests.common.models import BaseModel


class CallbackModel(BaseModel):
    """A callback will have, for example:

        {
             'response': {
                'domains': [
                    ...
                ]
             },
             ...
        }

    The COLLECTION_MODEL is the class which will deserialize the response field
    and is set by subclasses.
    """

    COLLECTION_MODEL = None

    @classmethod
    def from_dict(cls, data):
        model = super(CallbackModel, cls).from_dict(data)
        if hasattr(model, 'response'):
            model.response = cls.COLLECTION_MODEL.from_dict(model.response)
        return model
