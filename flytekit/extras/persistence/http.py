import os
import pathlib

import requests as _requests

from flytekit.common.exceptions import user as _user_exceptions
from flytekit.core.data_persistence import DataPersistence, DataPersistencePlugins
from flytekit.loggers import logger


class HttpPersistence(DataPersistence):
    """
    DataPersistence implementation for the HTTP protocol. only supports downloading from an http source. Uploads are
    not supported currently.
    """

    PROTOCOL_HTTP = "http"
    PROTOCOL_HTTPS = "https"
    _HTTP_OK = 200
    _HTTP_FORBIDDEN = 403
    _HTTP_NOT_FOUND = 404

    def __init__(self, *args, **kwargs):
        super(HttpPersistence, self).__init__(name="http/https", *args, **kwargs)

    def exists(self, path: str):
        rsp = _requests.head(path)
        allowed_codes = {
            type(self)._HTTP_OK,
            type(self)._HTTP_NOT_FOUND,
            type(self)._HTTP_FORBIDDEN,
        }
        if rsp.status_code not in allowed_codes:
            raise _user_exceptions.FlyteValueException(
                rsp.status_code,
                "Data at {} could not be checked for existence. Expected one of: {}".format(path, allowed_codes),
            )
        return rsp.status_code == type(self)._HTTP_OK

    def get(self, from_path: str, to_path: str, recursive: bool = False):
        if recursive:
            raise _user_exceptions.FlyteAssertion(
                "Reading data recursively from HTTP endpoint is not currently supported."
            )
        rsp = _requests.get(from_path)
        if rsp.status_code != type(self)._HTTP_OK:
            raise _user_exceptions.FlyteValueException(
                rsp.status_code,
                "Request for data @ {} failed. Expected status code {}".format(from_path, type(self)._HTTP_OK),
            )
        head, _ = os.path.split(to_path)
        if head and head.startswith("/"):
            logger.debug(f"HttpPersistence creating {head} so that parent dirs exist")
            pathlib.Path(head).mkdir(parents=True, exist_ok=True)
        with open(to_path, "wb") as writer:
            writer.write(rsp.content)

    def put(self, from_path: str, to_path: str, recursive: bool = False):
        raise _user_exceptions.FlyteAssertion("Writing data to HTTP endpoint is not currently supported.")

    def construct_path(self, add_protocol: bool, add_prefix: bool, *paths) -> str:
        raise _user_exceptions.FlyteAssertion(
            "There are multiple ways of creating http links / paths, this is not supported by the persistence layer"
        )


DataPersistencePlugins.register_plugin("http://", HttpPersistence)
DataPersistencePlugins.register_plugin("https://", HttpPersistence)
