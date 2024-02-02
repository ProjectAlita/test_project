#!/usr/bin/python3
# coding=utf-8

#   Copyright 2024 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Module """

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import module  # pylint: disable=E0611,E0401


class Module(module.ModuleModel):
    """ Pylon module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor

    def init(self):
        """ Init module """
        log.info("Initializing module")
        # Init
        self.descriptor.init_all(
            url_prefix="/",
            static_url_prefix="/",
        )

        from .tools.config import Config
        _config = Config(self)
        self.descriptor.register_tool('constants', _config)
        self.descriptor.register_tool('config', _config)

        from .tools import db
        self.descriptor.register_tool('db', db)

        from .tools import db_tools
        self.descriptor.register_tool('db_tools', db_tools)

        @self.context.app.teardown_appcontext
        def shutdown_session(exception=None):
            db.session.remove()

    def deinit(self):
        """ De-init module """
        log.info("De-initializing module")
        # De-init
        self.descriptor.deinit_all()
