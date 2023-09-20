import base64

from scrapy import version_info

if version_info >= (2, 6, 0):
    from scrapy.item import Item
else:
    from scrapy.item import _BaseItem as Item

from itemadapter import ItemAdapter, is_item
from scrapy.exporters import PythonItemExporter
from scrapy.utils.python import to_unicode


def pre_join(pre, key):
    if pre is None:
        return None
    if pre == "":
        return key
    return f"{pre}.{key}"


class TextDictKeyPythonItemExporter(PythonItemExporter):
    def __init__(self, ensure_base64=False, **kwargs):
        super(TextDictKeyPythonItemExporter, self).__init__(dont_fail=True, **kwargs)
        self.ensure_base64 = ensure_base64

    def _serialize_dict(self, value, pre=None, field_filter=None):
        for key, val in value.items():
            k = None
            if field_filter:
                if pre is not None:
                    k = pre_join(pre, key)
                    if k in field_filter:
                        continue
            yield to_unicode(key), self._serialize_value(
                val, pre=k, field_filter=field_filter
            )

    def _serialize_value(self, value, pre=None, field_filter=None):
        try:
            if isinstance(value, dict):
                return dict(
                    self._serialize_dict(value, pre=pre, field_filter=field_filter)
                )
            elif isinstance(value, Item):
                return self.export_item(value, pre=pre, field_filter=field_filter)
            elif is_item(value):
                return dict(self._serialize_item(value))
            value = super(TextDictKeyPythonItemExporter, self)._serialize_value(value)
        except UnicodeDecodeError as e:
            if self.ensure_base64 and isinstance(value, bytes):
                value = to_unicode(base64.b64encode(value))
            else:
                raise e
        return value

    def _get_serialized_fields(
        self, item, default_value=None, include_empty=None, pre=None, field_filter=None
    ):
        """Copy from BaseItemExporter
        """
        item = ItemAdapter(item)

        if include_empty is None:
            include_empty = self.export_empty_fields

        if self.fields_to_export is None:
            if include_empty:
                field_iter = item.field_names()
            else:
                field_iter = item.keys()
        else:
            if include_empty:
                field_iter = self.fields_to_export
            else:
                field_iter = (x for x in self.fields_to_export if x in item)

        for field_name in field_iter:
            k = None
            if field_filter:
                if pre is not None:
                    k = pre_join(pre, field_name)
                    if k in field_filter:
                        continue
            if field_name in item:
                field_meta = item.get_field_meta(field_name)
                value = self.serialize_field(
                    field_meta,
                    field_name,
                    item[field_name],
                    pre=k,
                    field_filter=field_filter,
                )
            else:
                value = default_value

            yield field_name, value

    def serialize_field(self, field, name, value, pre=None, field_filter=None):
        serializer = field.get("serializer", self._serialize_value)
        if serializer == self._serialize_value:
            return serializer(value, pre=name, field_filter=field_filter)
        return serializer(value)

    def _serialize_item(self, item, pre=None, field_filter=None):
        for key, value in ItemAdapter(item).items():
            k = None
            if field_filter:
                if pre is not None:
                    k = pre_join(pre, key)
                    if k in field_filter:
                        continue
            key = to_bytes(key) if self.binary else key
            yield key, self._serialize_value(value, pre=pre, field_filter=field_filter)

    def export_item(self, item, pre=None, field_filter=None):
        result = dict(
            self._get_serialized_fields(item, pre=pre, field_filter=field_filter)
        )
        if self.binary:
            result = dict(self._serialize_item(result))
        return result
