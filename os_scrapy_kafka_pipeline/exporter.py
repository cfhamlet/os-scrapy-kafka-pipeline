import base64

from scrapy.exporters import PythonItemExporter
from scrapy.utils.python import to_unicode


class TextDictKeyPythonItemExporter(PythonItemExporter):
    def __init__(self, ensure_base64=False, **kwargs):
        super(TextDictKeyPythonItemExporter, self).__init__(dont_fail=True, **kwargs)
        self.ensure_base64 = ensure_base64

    def _serialize_dict(self, value):
        for k, v in super(TextDictKeyPythonItemExporter, self)._serialize_dict(value):
            yield to_unicode(k), v

    def _serialize_value(self, value):
        try:
            value = super(TextDictKeyPythonItemExporter, self)._serialize_value(value)
        except UnicodeDecodeError as e:
            if self.ensure_base64 and isinstance(value, bytes):
                value = to_unicode(base64.encodebytes(value))
            else:
                raise e
        return value
