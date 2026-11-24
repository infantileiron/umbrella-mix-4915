import hashlib
import json
from datetime import date, datetime, timezone


def encode(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc).isoformat(timespec='seconds')
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f'Cannot encode {type(value).__name__}')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      default=encode, allow_nan=False)


def checksum(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
