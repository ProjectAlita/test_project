#!/usr/bin/python
# coding=utf-8

#     Copyright 2024 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

""" Secrets DB model """

# from sqlalchemy import Something  # pylint: disable=E0401
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask import abort

from tools import db, db_tools
from pylon.core.tools import log


class MetadataEntry(db_tools.AbstractBaseMixin, db.Base):  # pylint: disable=C0111
    __tablename__ = "metadata_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(20), unique=True)
    data: Mapped[str] = mapped_column(String(90))

    @staticmethod
    def get_all():
        return MetadataEntry.query.all()

    @staticmethod
    def get_by_key(key: str):
        return MetadataEntry.query.filter(MetadataEntry.key == key).first()

    @staticmethod
    def get_or_404(key: str):
        metadata_entry = MetadataEntry.query.filter(MetadataEntry.key == key).first()
        if not metadata_entry:
            abort(404, description="not found.")
        return metadata_entry

    @staticmethod
    def put(key: str, data: str):
        item = MetadataEntry.get_or_404(key)
        item.data = data
        item.commit()
        return item

    def commit(self) -> None:
        try:
            self._session.commit()
        except Exception as e:
            self.rollback()
            log.error(e)
            abort(422, description="rollback transaction on error.")

    def __repr__(self) -> str:
        return f"<metadata_entry(id={self.id}, key={self.key})>"
#
#     @property
#     def serialized(self):
#         raise RuntimeError("Not supported")
