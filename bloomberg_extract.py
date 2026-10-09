"""Bounded, cached Bloomberg requests for the WLS identifier export."""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import blpapi

CACHE = Path('wls_export/cache')

def request(service_name, operation, payload, cache_name):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (cache_name + '.json')
    if path.exists():
        cached = json.loads(path.read_text(encoding='utf-8'))
        if cached.get('payload') != payload or cached.get('operation') != operation or cached.get('service') != service_name:
            raise ValueError('Cache key conflicts with request: ' + str(path))
        return cached
    opts = blpapi.SessionOptions()
    opts.setServerHost('127.0.0.1')
    opts.setServerPort(8194)
    opts.setClientMode(blpapi.SessionOptions.DAPI)
    opts.setConnectTimeout(5000)
    opts.setNumStartAttempts(1)
    opts.setServiceCheckTimeout(5000)
    opts.setServiceDownloadTimeout(10000)
    session = blpapi.Session(opts)
    messages = []
    try:
        if not session.start():
            raise RuntimeError('Bloomberg session failed')
        if not session.openService(service_name):
            raise RuntimeError('Cannot open ' + service_name)
        req = session.getService(service_name).createRequest(operation)
        req.fromPy(payload)
        session.sendRequest(req)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            event = session.nextEvent(1000)
            if event.eventType() == blpapi.Event.REQUEST_STATUS:
                raise RuntimeError('; '.join(str(m) for m in event))
            if event.eventType() in (blpapi.Event.PARTIAL_RESPONSE, blpapi.Event.RESPONSE):
                for msg in event:
                    messages.append(msg.toPy())
                if event.eventType() == blpapi.Event.RESPONSE:
                    result = {'utc': datetime.now(timezone.utc).isoformat(),
                              'service': service_name, 'operation': operation,
                              'payload': payload, 'messages': messages}
                    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
                    return result
        raise TimeoutError('No complete response within 120 seconds; no automatic retry')
    finally:
        session.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['fields', 'members'])
    args = parser.parse_args()
    if args.mode == 'fields':
        result = request('//blp/apiflds', 'FieldInfoRequest', {
            'id': ['INDX_MEMBERS', 'INDX_MEMBERS2', 'INDX_MEMBERS3',
                   'COUNT_INDEX_MEMBERS', 'ID_EXCH_SYMBOL', 'TICKER', 'NAME',
                   'LONG_COMP_NAME', 'EXCH_CODE', 'EQY_PRIM_EXCH', 'ID_MIC_PRIM_EXCH'],
            'returnFieldDocumentation': True}, 'field_definitions_verified')
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        result = request('//blp/refdata', 'ReferenceDataRequest', {
            'securities': ['WLS Index'], 'fields': ['INDX_MEMBERS']}, 'members_1')
        for msg in result['messages']:
            if 'responseError' in msg:
                print(json.dumps(msg))
            for sec in msg.get('securityData', []):
                fd = sec.get('fieldData', {})
                print(json.dumps({**sec, 'fieldData': {k: {'rows': len(v), 'sample': v[:5]} if isinstance(v, list) else v for k,v in fd.items()}}, indent=2))
