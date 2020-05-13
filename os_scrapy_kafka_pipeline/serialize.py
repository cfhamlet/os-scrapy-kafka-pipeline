import base64

from scrapy.utils.python import to_unicode
from scrapy.utils.serialize import ScrapyJSONEncoder


class ScrapyJSNONBase64Encoder(ScrapyJSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return to_unicode(base64.encodebytes(o))
        return super(ScrapyJSNONBase64Encoder, self).default(o)
