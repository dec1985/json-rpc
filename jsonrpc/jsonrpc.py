﻿import json
import six


class JSONRPCProtocol(object):

    """ JSON-RPC protocol implementation."""

    JSONRPC_VERSION = "2.0"

    @classmethod
    def create_request(cls, method, params, _id=None):
        return JSONRPCRequest(method, params, _id=_id)

    @classmethod
    def parse_request(cls, json_str):
        return JSONRPCRequest.from_json(json_str)


class JSONRPCRequest(object):

    """ A rpc call is represented by sending a Request object to a Server.

    The Request object has the following members:

    jsonrpc: A String specifying the version of the JSON-RPC protocol. MUST be
        exactly "2.0".

    method: A String containing the name of the method to be invoked. Method
        names that begin with the word rpc followed by a period character
        (U+002E or ASCII 46) are reserved for rpc-internal methods and
        extensions and MUST NOT be used for anything else.

    params: A Structured value that holds the parameter values to be used
        during the invocation of the method. This member MAY be omitted.

    id: An identifier established by the Client that MUST contain a String,
        Number, or NULL value if included. If it is not included it is assumed
        to be a notification. The value SHOULD normally not be Null [1] and
        Numbers SHOULD NOT contain fractional parts [2].

    The Server MUST reply with the same value in the Response object if
    included. This member is used to correlate the context between the two
    objects.

    [1] The use of Null as a value for the id member in a Request object is
    discouraged, because this specification uses a value of Null for Responses
    with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null
    for Notifications this could cause confusion in handling.

    [2] Fractional parts may be problematic, since many decimal fractions
    cannot be represented exactly as binary fractions.

    """

    serialize = staticmethod(json.dumps)
    deserialize = staticmethod(json.loads)

    def __init__(self, method=None, params=None, _id=None):
        self._dict = dict(jsonrpc=self.jsonrpc)
        self.method = method
        self.params = params
        self._id = _id

    @property
    def jsonrpc(self):
        return JSONRPCProtocol.JSONRPC_VERSION

    def __get_method(self):
        return self._dict["method"]

    def __set_method(self, value):

        if not isinstance(value, six.string_types):
            raise ValueError("Method should be string")

        if value.startswith("rpc."):
            raise ValueError(
                "Method names that begin with the word rpc followed by a " +
                "period character (U+002E or ASCII 46) are reserved for " +
                "rpc-internal methods and extensions and MUST NOT be used " +
                "for anything else.")

        self._dict["method"] = str(value)

    method = property(__get_method, __set_method)

    def __get_params(self):
        return self._dict.get("params")

    def __set_params(self, value):
        if value is not None and not isinstance(value, (list, tuple, dict)):
            raise ValueError("Incorrect params {}".format(value))

        if isinstance(value, tuple):
            value = list(value)

        if value is not None:
            self._dict["params"] = value

    params = property(__get_params, __set_params)

    def __get_id(self):
        return self._dict.get("id")

    def __set_id(self, value):
        if value is not None and \
           not isinstance(value, six.string_types + six.integer_types):
            raise ValueError("id should be string or integer")

        if value is not None:
            self._dict["id"] = value

    _id = property(__get_id, __set_id)

    @property
    def is_notification(self):
        """ A Notification is a Request object without an "id" member.

        :return bool:

        """
        return self._id is None

    @property
    def args(self):
        return tuple(self.params) if isinstance(self.params, list) else ()

    @property
    def kwargs(self):
        return self.params if isinstance(self.params, dict) else {}

    @property
    def json(self):
        return self.serialize(self._dict)

    @classmethod
    def from_json(cls, json_str):
        data = cls.deserialize(json_str)
        data = [data] if not isinstance(data, list) else data

        result = [JSONRPCRequest(
            method=d["method"], params=d.get("params"), _id=d.get("id")
        ) for d in data]

        return result if len(result) > 1 else result[0]




    def respond_error(self, error):
        data = JSONRPCResponse(error=error, _id=self.id)._dict
        return self.serialize(data)

    def respond_success(self, result):
        data = JSONRPCResponse(result=result, _id=self.id)._dict
        return self.serialize(data)


class JSONRPCBatchRequest(object):
    def __init__(self, *requests):
        self.requests = requests

    @classmethod
    def from_json(cls, json_str):
        return JSONRPCRequest.from_json(json_str)

    @property
    def json(self):
        return json.dumps([r._dict for r in self.requests])


class JSONRPCResponse(object):

    """ JSON-RPC response object to JSONRPCRequest.

    When a rpc call is made, the Server MUST reply with a Response, except for
    in the case of Notifications. The Response is expressed as a single JSON
    Object, with the following members:

    jsonrpc: A String specifying the version of the JSON-RPC protocol. MUST be
        exactly "2.0".

    result: This member is REQUIRED on success.
        This member MUST NOT exist if there was an error invoking the method.
        The value of this member is determined by the method invoked on the
        Server.

    error: This member is REQUIRED on error.
        This member MUST NOT exist if there was no error triggered during
        invocation. The value for this member MUST be an Object.

    id: This member is REQUIRED.
        It MUST be the same as the value of the id member in the Request
        Object. If there was an error in detecting the id in the Request
        object (e.g. Parse error/Invalid Request), it MUST be Null.

    Either the result member or error member MUST be included, but both
    members MUST NOT be included.

    """

    serialize = staticmethod(json.dumps)

    def __init__(self, result=None, error=None, _id=None):
        self._dict = dict(jsonrpc=self.jsonrpc)

        if result is None and error is None:
            raise ValueError("Either result or error should be used")

        self.result = result
        self.error = error
        self._id = _id

    @property
    def jsonrpc(self):
        return JSONRPCProtocol.JSONRPC_VERSION

    def __get_result(self):
        return self._dict["result"]

    def __set_result(self, value):
        pass

    result = property(__get_result, __set_result)

    def __get_error(self):
        return self._dict["error"]

    def __set_error(self, value):
        pass

    error = property(__get_error, __set_error)

    def __get_id(self):
        return self._dict["_id"]

    def __set_id(self, value):
        if value is None:
            value = "null"

        if not isinstance(value, six.string_types + six.integer_types):
            raise ValueError("id should be string or integer")

        self._dict["id"] = value

    _id = property(__get_id, __set_id)

    @property
    def json(self):
        return self.serialize(self._dict)
