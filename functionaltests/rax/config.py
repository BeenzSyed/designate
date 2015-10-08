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

from functionaltests.common.config import cfg

cfg.CONF.register_group(cfg.OptGroup(
    name='rax', title='Configuration for rackspace-specific tests'
))

cfg.CONF.register_opts([
    cfg.StrOpt('auth_url', help="The identity endpoint"),
    cfg.StrOpt('username'),
    cfg.StrOpt('apikey'),
    cfg.StrOpt('tenant_name',
        help="The tenant name is the same as the id at rackspace"),
    cfg.StrOpt('endpoint', help="The classic api's endpoint"),
], group='rax')
