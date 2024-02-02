# pylint: disable=E1101,E0203,C0103
#
#   Copyright 2023 getcarrier.io
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

""" Config """

import json
from pylon.core.tools import log  # pylint: disable=E0401
from .patterns import SingletonABC


class Config(metaclass=SingletonABC):  # pylint: disable=R0903
    """ Config singleton """

    def __init__(self, module):
        module_cfg = module.descriptor.config
        self.load_settings(
            module_cfg.get("settings", {}),
            (
                ("DATABASE_VENDOR", "str", "postgres"),
                ("POSTGRES_HOST", "str", "postgres"),
                ("POSTGRES_PORT", "int", 5432),
                ("POSTGRES_USER", "str", ""),
                ("POSTGRES_PASSWORD", "str", ""),
                ("POSTGRES_DB", "str", ""),
                ("POSTGRES_SCHEMA", "str", "pylon"),
                ("POSTGRES_TENANT_SCHEMA", "str", "tenant"),
                ("DATABASE_URI", "str", None),
                ("DATABASE_ENGINE_OPTIONS", "dict", None),
            )
        )
        #
        # Make DB URI if not set
        #
        if self.DATABASE_ENGINE_OPTIONS is None:
            self.DATABASE_ENGINE_OPTIONS = {}
        #
        if self.DATABASE_URI is None:
            if self.DATABASE_VENDOR == "sqlite":  # Probably is not supported with tenant schemas now  # pylint: disable=C0301
                self.DATABASE_URI = f"sqlite:///{self.SQLITE_DB}"
                self.DATABASE_ENGINE_OPTIONS["isolation_level"] = "SERIALIZABLE"
            elif self.DATABASE_VENDOR == "postgres":
                self.DATABASE_URI = 'postgresql://{username}:{password}@{host}:{port}/{database}'.format(  # pylint: disable=C0301
                    host=self.POSTGRES_HOST,
                    port=self.POSTGRES_PORT,
                    username=self.POSTGRES_USER,
                    password=self.POSTGRES_PASSWORD,
                    database=self.POSTGRES_DB
                )
                if not self.DATABASE_ENGINE_OPTIONS:
                    self.DATABASE_ENGINE_OPTIONS = {
                        "isolation_level": "READ COMMITTED",
                        "echo": False,
                        "pool_size": 50,
                        "max_overflow": 100,
                        "pool_pre_ping": True
                    }
            else:
                raise RuntimeError(f"Unsupported DB vendor: {self.DATABASE_VENDOR}")
        #
        log.info('Initialized config %s', self)

    def load_settings(self, settings, schema):
        """ Load and set config vars """
        processors = {
            "str": lambda item: item if isinstance(item, str) else str(item),
            "int": lambda item: item if isinstance(item, int) else int(item),
            "bool": lambda item: item if isinstance(item, bool) else item.lower() in ["true", "yes"],  # pylint: disable=C0301
            "dict": lambda item: item if isinstance(item, dict) else json.loads(item),
        }
        #
        for item in schema:
            if len(item) == 3:
                key, kind, default = item
            elif len(item) == 2:
                key, kind = item
                default = ...
            else:
                raise RuntimeError(f"Invalid config schema: {item}")
            #
            if isinstance(default, set):
                default = getattr(self, list(default)[0])
            #
            data = ...
            for variant in [key, key.lower(), key.upper()]:
                if variant in settings:
                    data = settings[variant]
            #
            if data is ... and default is ...:
                raise RuntimeError(f"Required config value is not set: {key}")
            #
            if data is ...:
                data = default
            elif kind in processors:
                data = processors[kind](data)
            #
            setattr(self, key, data)
