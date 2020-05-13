from scrapy.exporters import PythonItemExporter
from scrapy.utils.python import to_unicode


class TextDictKeyPythonItemExporter(PythonItemExporter):
    def _serialize_dict(self, value):
        k, v = next(super(TextDictKeyPythonItemExporter, self)._serialize_dict(value))
        yield to_unicode(k), v
