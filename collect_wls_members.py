"""Use the user-approved paginated membership field; discard returned weights."""
import json
import math
from bloomberg_extract import request, CACHE
from build_wls_workbook import securities, OUT, get_first_members

count_data=request('//blp/refdata','ReferenceDataRequest',{
    'securities':['WLS Index'],'fields':['COUNT_INDEX_MEMBERS']},'member_count')
expected=next(securities(count_data))['fieldData']['COUNT_INDEX_MEMBERS']
members=[]
for page in range(1,math.ceil(expected/3000)+1):
    result=request('//blp/refdata','ReferenceDataRequest',{
        'securities':['WLS Index'],'fields':['INDEX_MEMBERS_WEIGHTS'],
        'overrides':[{'fieldId':'PAGE_NUMBER_OVERRIDE','value':str(page)}]},f'members_paged_{page}')
    for sec in securities(result):
        if sec.get('fieldExceptions') or sec.get('securityError'):
            raise RuntimeError(json.dumps(sec))
        records=sec.get('fieldData',{}).get('INDEX_MEMBERS_WEIGHTS',[])
        if not records:
            raise RuntimeError(f'No members on page {page}')
        for record in records:
            candidates=[k for k in record if 'ticker' in k.lower() or k == 'Index Member']
            if len(candidates)!=1:
                raise RuntimeError('Unexpected member columns: '+repr(list(record)))
            key=candidates[0]
            member=record[key]
            if not member.endswith(' Equity'):
                member += ' Equity'
            members.append(member)
            # Keep source member IDs, not the additional weight values.
            for column in list(record):
                if column!=key:
                    del record[column]
    result['retention_note']='Only constituent identifier columns retained; weights discarded after receipt.'
    (CACHE/f'members_paged_{page}.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Membership page {page}: cumulative {len(members):,}',flush=True)
if len(members)!=expected or len(set(members))!=expected:
    raise RuntimeError(f'Membership mismatch: rows={len(members)}, unique={len(set(members))}, expected={expected}')
if not set(get_first_members()).issubset(members):
    raise RuntimeError('Paged membership disagrees with first identifier-only page')
(OUT/'members_complete.json').write_text(json.dumps(members,indent=2,ensure_ascii=False),encoding='utf-8')
print(f'PASS: all {expected:,} unique constituents reconciled to Bloomberg count.')
