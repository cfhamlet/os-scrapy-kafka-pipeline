import base64

from scrapy.exporters import PythonItemExporter
from scrapy.utils.python import to_unicode


class TextDictKeyPythonItemExporter(PythonItemExporter):
    def _serialize_dict(self, value):
        k, v = next(super(TextDictKeyPythonItemExporter, self)._serialize_dict(value))
        yield to_unicode(k), v

    def _serialize_value(self, value):
        try:
            value = super(TextDictKeyPythonItemExporter, self)._serialize_value(value)
        except UnicodeDecodeError as e:
            if isinstance(value, bytes):
                value = to_unicode(base64.encodebytes(value))
            else:
                raise e
        return value
