import sys, zipfile, datetime as dt, re
from lxml import etree
import openpyxl
SRC, CALC, OUT = sys.argv[1:4]
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
calc = openpyxl.load_workbook(CALC, data_only=True)
src = openpyxl.load_workbook(SRC)          # só para mapear nomes de abas -> arquivos
zin = zipfile.ZipFile(SRC)
wbxml = etree.fromstring(zin.read('xl/workbook.xml'))
rels = etree.fromstring(zin.read('xl/_rels/workbook.xml.rels'))
rid2t = {r.get('Id'): r.get('Target') for r in rels}
sheetfile = {}
for s in wbxml.find('m:sheets', NS):
    rid = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    t = rid2t[rid]; sheetfile['xl/' + t.lstrip('/').replace('xl/', '')] = s.get('name')
def serial(d): return (d - dt.datetime(1899, 12, 30)).total_seconds() / 86400
zout = zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED)
n = 0
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename in sheetfile:
        ws = calc[sheetfile[item.filename]]
        root = etree.fromstring(data)
        for c in root.iter('{%s}c' % NS['m']):
            f = c.find('m:f', NS)
            if f is None: continue
            val = ws[c.get('r')].value
            v = c.find('m:v', NS)
            if v is None: v = etree.SubElement(c, '{%s}v' % NS['m'])
            if isinstance(val, dt.datetime): v.text = repr(serial(val)).rstrip('0').rstrip('.') ; c.attrib.pop('t', None)
            elif isinstance(val, bool): v.text = '1' if val else '0'; c.set('t', 'b')
            elif isinstance(val, (int, float)): v.text = repr(val); c.attrib.pop('t', None)
            elif val is None: c.remove(v)
            else: v.text = str(val); c.set('t', 'str')
            n += 1
        data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    zout.writestr(item, data)
zout.close(); print('cached', n)
