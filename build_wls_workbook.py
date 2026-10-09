"""Build a listing-level WLS workbook from cached identifier-only requests."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from bloomberg_extract import request, CACHE

OUT = Path('wls_export')
FIELDS = ['ID_EXCH_SYMBOL', 'LONG_COMP_NAME', 'PRIMARY_EXCHANGE_NAME', 'ID_MIC_PRIM_EXCH']

def securities(result):
    for msg in result['messages']:
        if msg.get('responseError'):
            raise RuntimeError(json.dumps(msg['responseError']))
        yield from msg.get('securityData', [])

def get_first_members():
    result = request('//blp/refdata','ReferenceDataRequest',{
        'securities':['WLS Index'],'fields':['INDX_MEMBERS']},'members_1')
    return [v['Member Ticker and Exchange Code'] + ' Equity'
            for s in securities(result) for v in s['fieldData']['INDX_MEMBERS']]

def collect_identifiers(members):
    collected = {}
    # Reuse the initial field-validation sample where it overlaps membership.
    pilot = CACHE / 'identifier_pilot.json'
    if pilot.exists():
        for sec in securities(json.loads(pilot.read_text(encoding='utf-8'))):
            if sec['security'] in members:
                collected[sec['security']] = sec
    for file in sorted(CACHE.glob('identifiers_*.json')):
        result = json.loads(file.read_text(encoding='utf-8'))
        if result['payload']['fields'] == FIELDS:
            for sec in securities(result):
                if sec['security'] in members:
                    collected[sec['security']] = sec
    missing = [s for s in members if s not in collected]
    for offset in range(0, len(missing), 250):
        batch = missing[offset:offset+250]
        key = hashlib.sha256('\n'.join(batch).encode()).hexdigest()[:16]
        result = request('//blp/refdata', 'ReferenceDataRequest',
                         {'securities': batch, 'fields': FIELDS}, 'identifiers_' + key)
        for sec in securities(result):
            errors = json.dumps(sec.get('fieldExceptions', [])) + json.dumps(sec.get('securityError', {}))
            if any(token in errors.upper() for token in ['LIMIT', 'MAX_REQUEST', 'NOT_ENTITLED']):
                raise RuntimeError('Stopped on limit/entitlement error: ' + errors)
            collected[sec['security']] = sec
        print(f'Identifiers cached: {len(collected):,}/{len(members):,}', flush=True)
    if set(members) != set(collected):
        raise RuntimeError('Missing or unexpected securities in identifier responses')
    return collected

def build(members, collected):
    count_result = json.loads((CACHE / 'member_count.json').read_text(encoding='utf-8'))
    expected = next(securities(count_result))['fieldData']['COUNT_INDEX_MEMBERS']
    if len(members) != len(set(members)):
        raise RuntimeError('Duplicate source member identifiers; investigate before export')
    rows = []
    for source_id in members:
        sec = collected[source_id]
        fd = sec.get('fieldData', {})
        vals = [str(fd.get(f, '') or '') for f in FIELDS]
        labels = ['local exchange ticker', 'company name', 'exchange name', 'exchange MIC']
        problems = ['Bloomberg did not return ' + label for label,v in zip(labels,vals) if not v]
        if sec.get('securityError'):
            problems.append('Security error: ' + json.dumps(sec['securityError']))
        if sec.get('fieldExceptions'):
            descriptions = sorted({e.get('errorInfo',{}).get('message','Unspecified field error') for e in sec['fieldExceptions']})
            problems.append('Source explanation: ' + '; '.join(descriptions))
        rows.append({'source':source_id, 'vals':vals, 'problems':problems})
    pair_counts = Counter((r['vals'][0],r['vals'][3]) for r in rows if r['vals'][0] and r['vals'][3])
    for row in rows:
        if pair_counts.get((row['vals'][0],row['vals'][3]),0) > 1:
            row['problems'].append('Repeated exchange ticker + MIC; distinct source listings retained')
    rows.sort(key=lambda r:(r['vals'][1].casefold(),r['vals'][3],r['vals'][0],r['source']))
    wb = Workbook()
    stocks = wb.active
    stocks.title = 'Stocks'
    stocks.append(['Listing ID','Exchange ticker','Company name','Exchange / trading venue','Exchange MIC','Review note'])
    audit = wb.create_sheet('Source mapping')
    audit.append(['Listing ID','Bloomberg member identifier','Exchange ticker','Exchange MIC'])
    issues = wb.create_sheet('Review')
    issues.append(['Listing ID','Company name','Bloomberg member identifier','Review note'])
    for number,row in enumerate(rows,1):
        note = '; '.join(row['problems'])
        stocks.append([number,*row['vals'],note])
        audit.append([number,row['source'],row['vals'][0],row['vals'][3]])
        if note:
            issues.append([number,row['vals'][1],row['source'],note])
    notes = wb.create_sheet('Read me')
    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    status = 'COMPLETE: count reconciles' if len(rows)==expected else 'PARTIAL: missing constituents'
    for row in [
        ['Item','Details'], ['Index','WLS Index'], ['Export time (Singapore)',now],
        ['Coverage',status], ['Bloomberg member count',expected], ['Exported listings',len(rows)],
        ['Rows requiring review',issues.max_row-1],
        ['Scope','One row per index constituent security/listing, not one per unique company. Share classes and multiple listings remain separate.'],
        ['Exchange ticker','ID_EXCH_SYMBOL: official local exchange symbol as supplied by Bloomberg. Not the generic Bloomberg TICKER field.'],
        ['Company name','LONG_COMP_NAME: legal company name, formatted by Bloomberg.'],
        ['Exchange / trading venue','PRIMARY_EXCHANGE_NAME and ID_MIC_PRIM_EXCH refer to the constituent listing. Stock Connect routes can appear as venues.'],
        ['Matching to Capital IQ','Use ticker plus exchange and company name. This is not a prevalidated Capital IQ identifier file; provider-specific mapping may still be needed.'],
        ['Text preservation','Ticker cells are text, preserving leading zeros, punctuation and non-Latin characters.'],
        ['Missing values','Blank values are left blank and flagged. No fabricated symbols or automatic substitution with Bloomberg tickers.'],
        ['Duplicates','No deduplication by company name or ticker. Review flags repeated ticker+MIC pairs.'],
        ['Source','Bloomberg Desktop API //blp/refdata. Cached responses and request timestamps are in wls_export/cache. Membership weights were discarded.'],
        ['Membership retrieval','INDEX_MEMBERS_WEIGHTS, paginated in blocks of 3,000, with user approval. Only constituent identifiers retained. Cross-checked against COUNT_INDEX_MEMBERS and the first 2,500 INDX_MEMBERS.'],
        ['Security data requested','Only ID_EXCH_SYMBOL, LONG_COMP_NAME, PRIMARY_EXCHANGE_NAME and ID_MIC_PRIM_EXCH. No security prices, financial statements, or history requested.'],
        ['Freshness','Current membership retrieved on 9 October 2026; not a guaranteed snapshot for the 12 October start.'],
        ['Validation','Unique source identifiers checked, member count reconciled, missing values flagged, and workbook reopened to verify all ticker cells.'],
    ]:
        notes.append(row)
    for sheet in wb:
        sheet.freeze_panes='A2'
        sheet.sheet_view.showGridLines=False
        for cell in sheet[1]:
            cell.fill=PatternFill('solid',fgColor='17365D')
            cell.font=Font(color='FFFFFF',bold=True)
            cell.alignment=Alignment(wrap_text=True,vertical='center')
        sheet.row_dimensions[1].height=30
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value,str):
                    cell.data_type='s'
                    cell.number_format='@'
        if sheet.max_row>1:
            table=Table(displayName=sheet.title.replace(' ','')+'Table',ref=sheet.dimensions)
            table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True)
            sheet.add_table(table)
    for col,width in {'A':12,'B':22,'C':58,'D':28,'E':18,'F':75}.items(): stocks.column_dimensions[col].width=width
    for col,width in {'A':12,'B':36,'C':22,'D':18}.items(): audit.column_dimensions[col].width=width
    for col,width in {'A':12,'B':40,'C':32,'D':100}.items(): issues.column_dimensions[col].width=width
    notes.column_dimensions['A'].width=29
    notes.column_dimensions['B'].width=110
    for row in notes.iter_rows(min_row=2):
        row[1].alignment=Alignment(wrap_text=True,vertical='top')
        notes.row_dimensions[row[0].row].height=45
    path=OUT / 'WLS_Stocks_2026-10-09.xlsx'
    wb.save(path)
    check=load_workbook(path,read_only=True,data_only=False)
    actual=list(check['Stocks'].iter_rows(min_row=2,values_only=True))
    assert len(actual)==len(rows)
    for exported,source in zip(actual,rows):
        assert (exported[1] or '')==source['vals'][0]
        assert (exported[2] or '')==source['vals'][1]
    check.close()
    summary={'file':str(path),'expected_members':expected,'exported_rows':len(rows),
             'review_rows':issues.max_row-1,'missing_by_field':{f:sum(not r['vals'][i] for r in rows) for i,f in enumerate(FIELDS)},
             'duplicate_ticker_mic_groups':sum(n>1 for n in pair_counts.values()),
             'sample':[{'ticker':r['vals'][0],'name':r['vals'][1],'exchange':r['vals'][2]} for r in rows[:5]]}
    (OUT/'validation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--first-only',action='store_true',help='Cache identifiers for the already retrieved first page only; do not export.')
    a=p.parse_args()
    members=get_first_members() if a.first_only else json.loads((OUT/'members_complete.json').read_text(encoding='utf-8'))
    data=collect_identifiers(members)
    if not a.first_only:
        build(members,data)
