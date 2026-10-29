"""Gera o KOM PN 2027 (RL e RT) sobre o template oficial KOM_Template (PMO-ETO)."""
import sys, copy
from datetime import date, timedelta
from lxml import etree
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from model import *

TEMPLATE, OUT = sys.argv[1], sys.argv[2]
P = build()
NAVY, ORANGE, TEAL, GREEN, GREY, TXT = '1F1F4C', 'F47B20', '009FC2', '628C0E', '989898', '4D4D4D'
PROJ = 'PN 2027'
PROJ_NOME = 'Instalação de Equipamentos Especiais (RL e RT)'
GP = 'Sandro Padilha'
KOM_DATE = '29/10/2026'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'

def brl(v, dec=0):
    s = f'{v:,.{dec}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

def d8(d): return d.strftime('%d/%m/%y')
def d5(d): return d.strftime('%d/%m')

# --------------------------------------------------------------- derivados do modelo
tot_1010 = sum(p['b_1010'] for p in P)
tot_ago = sum(p['b_ago'] for p in P)

def curva(p):
    """Mesma fórmula da aba 'Curva orçamentária' (material no mês do início + serviço rateado na execução)."""
    S, E = p['S'], p['sched']['exec'][1]
    dur = (E - S).days
    out = []
    for m in range(1, 13):
        ms = date(2027, m, 1); nx = date(2027, m + 1, 1) if m < 12 else date(2028, 1, 1)
        mat = MAT_PCT if (S.year == 2027 and S.month == m) else 0
        ov = max(0, (min(E, nx) - max(S, ms)).days)
        out.append(p['b_1010'] * (mat + (1 - MAT_PCT) * ov / dur))
    return out
for p in P: p['curva'] = curva(p)
tot_m = [sum(p['curva'][m] for p in P) for m in range(12)]
assert abs(sum(tot_m) - tot_1010) < 1
lin = {}
import openpyxl
_cad = openpyxl.load_workbook('/tmp/claude-0/-home-user-proposta-comercial/9da2235d-c067-5426-823d-b6e1ef8d168f/scratchpad/zip/Cadastro_CAPEX_2027_2029_24 08 2026_PMO.xlsx', data_only=True)['Mensalização Capex 08.10']
for r_ in _cad.iter_rows(min_row=2, values_only=True):
    if r_[1] in {p['sigco'] for p in P} and r_[3] == 'DCMD': lin[r_[1]] = list(r_[4:16])
lin_m = [sum(lin[p['sigco']][m] for p in P) for m in range(12)]

prs = Presentation(TEMPLATE)
S_ = list(prs.slides)   # slides originais (0-based): 0 capa,1 dados,2 MT,3 AT,4 curva,5 prem,6 conceito,7 riscos,8 macro,9 detalhado,10 vazio,11 obrigado

# --------------------------------------------------------------- helpers
def shp(slide, name, left=None, top=None, nth=0):
    c = [s for s in slide.shapes if s.name == name and (left is None or s.left == left) and (top is None or s.top == top)]
    return c[nth]

def drop(sh): sh._element.getparent().remove(sh._element)

def set_runs(par, text):
    """Mantém a formatação do 1º run, troca o texto e remove os demais."""
    runs = par.runs
    if not runs:
        r = par.add_run(); r.text = text; return r
    runs[0].text = text
    for r in runs[1:]: r._r.getparent().remove(r._r)
    return runs[0]

def set_text(sh, text):
    set_runs(sh.text_frame.paragraphs[0], text)

def set_paras(sh, texts):
    """Uma entrada por parágrafo; clona o último parágrafo se faltar e apaga os que sobram."""
    tb = sh.text_frame._txBody
    ps = tb.findall(qn('a:p'))
    while len(ps) < len(texts):
        n = copy.deepcopy(ps[-1]); ps[-1].addnext(n); ps = tb.findall(qn('a:p'))
    for i, p_ in enumerate(ps):
        if i < len(texts):
            set_runs(sh.text_frame.paragraphs[i], texts[i])
        else:
            tb.remove(p_)

def clean_guidance(slide, keep=()):
    for s in list(slide.shapes):
        x = etree.tostring(s._element).decode()
        if s.name in keep: continue
        if 'accent5' in x or '<a:highlight>' in x:
            drop(s)

def rgb(h): return RGBColor.from_string(h)

def add_text(slide, x, y, w, h, text, size=9, bold=False, color=TXT, align='l', anchor='t', italic=False, wrap=True):
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = tb.text_frame; tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p_ = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[align]
        r = p_.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic; r.font.name = 'DM Sans'; r.font.color.rgb = rgb(color)
    return tb

def add_rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, lw=0.5):
    s = slide.shapes.add_shape(shape, Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h)))
    if fill is None: s.fill.background()
    else: s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    if line is None: s.line.fill.background()
    else: s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
    s.shadow.inherit = False
    return s

def strip_ext(el):
    for e in el.iter(qn('a:extLst')):
        pass
    for e in list(el.iter(qn('a:extLst'))):
        e.getparent().remove(e)

def cell_text(tc, text, size, bold=False, color=TXT, align='l'):
    txb = tc.find(qn('a:txBody'))
    for p_ in txb.findall(qn('a:p'))[1:]: txb.remove(p_)
    p_ = txb.find(qn('a:p'))
    for ch in list(p_): p_.remove(ch)
    ppr = etree.SubElement(p_, qn('a:pPr')); ppr.set('algn', align)
    r = etree.SubElement(p_, qn('a:r'))
    rpr = etree.SubElement(r, qn('a:rPr')); rpr.set('lang', 'pt-BR'); rpr.set('sz', str(int(size * 100))); rpr.set('b', '1' if bold else '0'); rpr.set('i', '0')
    sf = etree.SubElement(rpr, qn('a:solidFill')); c = etree.SubElement(sf, qn('a:srgbClr')); c.set('val', color)
    lt = etree.SubElement(rpr, qn('a:latin')); lt.set('typeface', 'DM Sans')
    t = etree.SubElement(r, qn('a:t')); t.text = text

def cell_fill(tc, hexcolor):
    tcpr = tc.find(qn('a:tcPr'))
    for sf in tcpr.findall(qn('a:solidFill')): tcpr.remove(sf)
    for nf in tcpr.findall(qn('a:noFill')): tcpr.remove(nf)
    sf = etree.SubElement(tcpr, qn('a:solidFill')); c = etree.SubElement(sf, qn('a:srgbClr')); c.set('val', hexcolor)

def rebuild_table(slide, src_frame, left, top, col_w, rows, row_h, size, hdr_size=None, aligns=None, bold_first=True, bold_rows=(), fills=None, name=None):
    """Clona uma tabela do template (estilo/bordas) e a reconstrói com novas colunas/linhas.
       rows[0] = cabeçalho. fills: {row_idx: hex}."""
    fr = copy.deepcopy(src_frame._element)
    slide.shapes._spTree.append(fr)
    tbl = fr.find('.//' + qn('a:tbl'))
    trs = tbl.findall(qn('a:tr'))
    htc = copy.deepcopy(trs[0].findall(qn('a:tc'))[0])
    btc = copy.deepcopy(trs[1].findall(qn('a:tc'))[0])
    for e in list(tbl):
        if e.tag in (qn('a:tr'),): tbl.remove(e)
    grid = tbl.find(qn('a:tblGrid'))
    for g in list(grid): grid.remove(g)
    for w in col_w:
        g = etree.SubElement(grid, qn('a:gridCol')); g.set('w', str(int(w)))
    hdr_size = hdr_size or size
    aligns = aligns or ['l'] + ['c'] * (len(col_w) - 1)
    for ri, row in enumerate(rows):
        tr = etree.SubElement(tbl, qn('a:tr')); tr.set('h', str(int(row_h if ri else row_h)))
        for ci, val in enumerate(row):
            tc = copy.deepcopy(htc if ri == 0 else btc); strip_ext(tc)
            if ri == 0: cell_text(tc, val, hdr_size, True, NAVY, aligns[ci] if aligns[ci] != 'l' else 'l')
            else:
                b = (bold_first and ci == 0) or ri in bold_rows
                cell_text(tc, val, size, b, NAVY if b else TXT, aligns[ci])
                cell_fill(tc, (fills or {}).get(ri, 'FFFFFF'))
            tr.append(tc)
    nv = fr.find('.//' + qn('p:cNvPr'))
    if name: nv.set('name', name)
    nv.set('id', str(max(int(x.get('id')) for x in slide.shapes._spTree.iter(qn('p:cNvPr'))) + 1))
    xf = fr.find(qn('p:xfrm'))
    xf.find(qn('a:off')).set('x', str(int(left))); xf.find(qn('a:off')).set('y', str(int(top)))
    xf.find(qn('a:ext')).set('cx', str(int(sum(col_w)))); xf.find(qn('a:ext')).set('cy', str(int(row_h * len(rows))))
    return fr

def footer(slide, num, label=None):
    for s in slide.shapes:
        if s.name == 'Rodapé':
            pr = s.text_frame.paragraphs[0]; rs = pr.runs
            rs[0].text = f'{num:02d}'
            for r in rs[1:-1]: pass
            # runs: [nº parte1, nº parte2?, ' · ', nome]
            txt = [r for r in rs]
            # reescreve: 1º run = número, remove runs intermediários de número, último = nome
            sep_i = [i for i, r in enumerate(rs) if '·' in r.text][0]
            for r in rs[1:sep_i]: r._r.getparent().remove(r._r)
            rs = pr.runs
            rs[-1].text = label or f'{PROJ} – {PROJ_NOME.upper()}'
            return

def eyebrow(slide, extra=f'{PROJ} · 12 SIGCOs'):
    for s in slide.shapes:
        if s.name == 'Eyebrow':
            rs = s.text_frame.paragraphs[0].runs
            if len(rs) >= 3:
                rs[1].text = f'   |   {extra}'
                for r in rs[2:]: r._r.getparent().remove(r._r)

# datas resumo
S_min = min(p['S'] for p in P)
exec_end_max = max(p['sched']['exec'][1] for p in P)
com_min = min(p['sched']['com'][0] for p in P); op_min = min(p['sched']['op'] for p in P); op_max = max(p['sched']['op'] for p in P)
ec_max = max(p['sched']['ec'][1] for p in P)
n_rt = sum(p['rt'] for p in P)    # 9
n_rl = sum(p['rl'] for p in P)    # 13 (12 novos + 1 remanejado)

# =============================================================== Slide 1 — Capa
s1 = S_[0]
set_text(shp(s1, 'Selo código'), PROJ)
set_text(shp(s1, 'Capa – projeto'), PROJ_NOME)
shp(s1, 'Capa – projeto').width = Emu(6100000)
shp(s1, 'Capa – projeto').text_frame.paragraphs[0].runs[0].font.size = Pt(18)
for s in s1.shapes:
    if s.name.startswith('Pílula GERENTE'): set_runs(s.text_frame.paragraphs[1], GP)
    if s.name.startswith('Pílula DATA'): set_runs(s.text_frame.paragraphs[1], KOM_DATE)
clean_guidance(s1)

# =============================================================== Slide 2 — Dados Básicos
s2 = S_[1]
set_text(shp(s2, 'Id código'), PROJ)
set_text(shp(s2, 'Id nome'), f'{PROJ_NOME} – 12 SIGCOs')
shp(s2, 'Id nome').text_frame.paragraphs[0].runs[0].font.size = Pt(13)
for s in s2.shapes:
    if s.name == 'Id GERENTE DO PROJETO': set_runs(s.text_frame.paragraphs[1], GP)
    if s.name == 'Id DEPARTAMENTO': set_runs(s.text_frame.paragraphs[1], 'DCMD')
    if s.name == 'Id OBJETIVO E DESTINAÇÃO': set_runs(s.text_frame.paragraphs[1], 'Qualidade do Produto e do Serviço – Conforme dados do PN')
esc = shp(s2, 'Escopo texto', top=2148840)
set_text(esc, (f'Instalação de {n_rt} reguladores de tensão (RT) e {n_rl-1} religadores (RL) novos, com remanejamento de 1 RL e instalação de 3 TripSavers, '
               'em 12 SIGCOs de alimentadores de 13,8 e 34,5 kV nas regionais da ETO: 6 SIGCOs para elevação do nível de tensão (QP) e 6 estudos de qualidade de serviço (QS). '
               'Maior pacote: SIGCO 90811 – LD UHE Isamu – Ponte Alta (4 RL + 3 RT, 0,25 km de RD MT e 2 chaves faca).'))
esc.text_frame.paragraphs[0].runs[0].font.size = Pt(10.5)
esc.text_frame.word_wrap = True
tot = shp(s2, 'Orç total')
rs = tot.text_frame.paragraphs[0].runs
rs[1].text = brl(tot_1010)
for r in rs[2:]: r._r.getparent().remove(r._r)
rs[1].font.size = Pt(28)
# subtexto do orçamento (clona o estilo do 'Ben texto')
ben_t = shp(s2, 'Ben texto')
orc_sub = copy.deepcopy(ben_t._element); s2.shapes._spTree.append(orc_sub)
sub = s2.shapes[-1]; sub.left = Emu(4709159); sub.top = Emu(5074920); sub.width = Emu(2986887)
set_text(sub, f'12 SIGCOs · Orçamento 08.10 (CAPEX 2027). Base Agosto: R$ {brl(tot_ago)} (Δ −R$ {brl(tot_ago-tot_1010)}).')
sub.text_frame.paragraphs[0].runs[0].font.size = Pt(10.5)
sub.name = 'Orç texto'
set_text(shp(s2, 'Ben rótulo'), 'NÍVEL DE TENSÃO – 6 ALIMENTADORES COM RT')
kr = shp(s2, 'Ben KPI').text_frame.paragraphs[0].runs
kr[0].text = '0,92'; kr[2].text = '0,96 '
set_text(ben_t, ('Elevação média do nível de tensão (faixa inicial 0,91–0,93 pu; meta 0,945–0,97 pu). '
                 'Os 6 estudos de QS reduzem DEC/FEC dos conjuntos atendidos.'))
ben_t.text_frame.paragraphs[0].runs[0].font.size = Pt(10.5)
eyebrow(s2); footer(s2, 2)
clean_guidance(s2)

# =============================================================== Slide 3 — Resumo MT
s3 = S_[2]
set_text(shp(s3, 'Title 2'), f'{PROJ} – {PROJ_NOME}')
for s in s3.shapes:
    if s.name == 'Dados da reunião':
        rs = s.text_frame.paragraphs[0].runs; rs[-1].text = GP
prem = [
 'O projeto será executado conforme orçamento aprovado.',
 'EPS mobilizará somente após geração e assinatura da O.S.',
 'Prazos conforme histórico PN 2026 de instalação de RL/RT (30 dias de execução por pacote de até 4 equipamentos; 45 dias para 5 ou mais).',
 'Contratação de empresas com capacidade técnica e financeira para execução das obras.',
 'Aprovação das LSS dentro do prazo solicitado, garantindo continuidade na execução das atividades.',
 'Cumprimento do prazo de 10 dias corridos para análise da documentação de colaboradores terceiros pelo SESMT ETO.',
 'Manutenção do escopo do projeto, sem inclusão de serviços não previstos inicialmente.',
 'Ausência de acidentes de trabalho que ocasionem paralisação das atividades.',
 'EPS atender a todos os procedimentos de segurança e às ITs.',
 'Recebimento de materiais e equipamentos conforme datas previstas na WBS, com alta assertividade no forecast financeiro.',
 'Disponibilidade de equipe de Linha Viva ETO, garantindo continuidade nas atividades em áreas energizadas.']
restr = ['Iniciar a obra somente após assinatura do contrato de prestação de serviços com a empreiteira executora.',
         'Encerramento contábil somente após fiscalização da Gestão de Ativos.',
         'Encerramento contábil até, no máximo, 17/11/2027.',
         'Energização até o mês-meta do TM (abr a ago/27).']
risk5 = ['Atraso na entrega de RL/RT (lead time de fornecimento).',
         'Indisponibilidade da equipe de Linha Viva / frentes simultâneas.',
         'Atraso na aprovação de LSS / documentação SESMT.',
         'Atraso no comissionamento e ajuste de proteção.',
         'Acidente de trabalho com paralisação da obra.']
set_paras(shp(s3, 'Premissas lista'), prem)
set_paras(shp(s3, 'Restrições lista'), restr)
set_paras(shp(s3, 'Riscos lista'), risk5)
set_text(shp(s3, 'Interface AT MT – título'), 'Datas de Interface – MT')
# tabela de interface
ti = shp(s3, 'Tabela interface').table
ifc = [('MT', 'Execução / desligamento programado', f'{d5(S_min)} a {d5(exec_end_max)}', 'EPS / DEOP', 'A iniciar'),
       ('MT', 'Ajuste de proteção e parametrização', f'{d5(com_min)} a {d5(op_max)}', 'DEOP', 'A iniciar'),
       ('MT', 'Comissionamento dos equipamentos', f'{d5(com_min)} a {d5(op_max)}', 'DMSL', 'A iniciar'),
       ('MT', 'Equipamentos em operação / energização', f'{d5(op_min)} a {d5(op_max)}', 'DMSL / DEOP', 'A iniciar')]
for ri, row in enumerate(ifc, 1):
    for ci, v in enumerate(row):
        tc = ti._tbl.tr_lst[ri].tc_lst[ci]
        cell_text(tc, v, 7 if ci in (1,) else 7.5, ci == 0, NAVY if ci == 0 else TXT, 'l' if ci < 2 else 'c')
# curva (3 linhas)
tcv = shp(s3, 'Tabela curva orçamentária').table
def k(v): return '–' if v < 500 and v == 0 else brl(v / 1000)
acc = 0; accs = []
for v in tot_m: acc += v; accs.append(acc)
rows3 = [['12', 'Curva WBS'] + [('–' if v == 0 else brl(v / 1000)) for v in tot_m] + [brl(tot_1010 / 1000)],
         ['', 'Acumulado'] + [('–' if v == 0 else brl(v / 1000)) for v in accs] + [brl(tot_1010 / 1000)],
         ['', 'Cad. 08.10'] + [brl(v / 1000) for v in lin_m] + [brl(sum(lin_m) / 1000)]]
for ri, row in enumerate(rows3, 1):
    for ci, v in enumerate(row):
        tc = tcv._tbl.tr_lst[ri].tc_lst[ci]
        cell_text(tc, v, 6.5 if ci < 2 or ci == 14 else 5.5, ci in (0, 1, 14), NAVY if ci in (0, 1, 14) else TXT, 'l' if ci < 2 else 'c')
        tcp = tc.find(qn('a:tcPr')); tcp.set('marL', '9144'); tcp.set('marR', '9144')
# aquisições
tq = shp(s3, 'Tabela aquisições').table
aq = [(f'RT ({n_rt}), RL ({n_rl}) e TripSaver (3)', 'Equipamento', d8(S_min), 'A confirmar'),
      ('Materiais complementares (WBS)', 'Material', d8(S_min), 'A confirmar'),
      ('Empreiteira executora (EPS)', 'Contratação', d8(S_min), 'A confirmar')]
for ri, row in enumerate(aq, 1):
    for ci, v in enumerate(row):
        tc = tq._tbl.tr_lst[ri].tc_lst[ci]
        cell_text(tc, v, 7.5, False, TXT, 'l' if ci == 0 else 'c')
clean_guidance(s3)

# =============================================================== Slide 5 — Curva orçamentária (detalhe)
s5 = S_[4]
src = shp(s3, 'Tabela curva orçamentária')
months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
rows = [['SIGCO', 'Projeto'] + months + ['Total']]
for p in P:
    rows.append([str(p['sigco']), p['ab']] + [('–' if v < 500 else brl(v / 1000)) for v in p['curva']] + [brl(p['b_1010'] / 1000)])
rows.append(['', 'Total – curva WBS'] + [('–' if v < 500 else brl(v / 1000)) for v in tot_m] + [brl(tot_1010 / 1000)])
rows.append(['', 'Acumulado – curva WBS'] + [('–' if v < 500 else brl(v / 1000)) for v in accs] + [brl(tot_1010 / 1000)])
rows.append(['', 'Cadastro 08.10 (rateio linear)'] + [brl(v / 1000) for v in lin_m] + [brl(sum(lin_m) / 1000)])
colw = [560000, 2400000] + [575000] * 12 + [800000]
nrows = len(rows)
rebuild_table(s5, src, 457200, 1215000, colw, rows, 262000, 8, 8, ['l', 'l'] + ['r'] * 13, True,
              bold_rows=(13, 14), fills={13: 'E6E6E6', 14: 'F3F5F8', 15: 'FFFFFF'}, name='Tabela curva detalhada')
add_text(s5, 457200, 5780000, 11270000, 500000,
         [f'Valores em R$ mil · Total aprovado: R$ {brl(tot_1010)} (Orçamento 08.10 do Cadastro CAPEX 2027–2029; Orçamento Agosto: R$ {brl(tot_ago)}).',
          'Curva alinhada à WBS (proposta): material (60%) no mês de início da execução e serviço (40%) rateado pelos dias de execução. '
          'Como no KOM 2026, o SIACO deve ser atualizado para coincidir com a curva da WBS (cadastro atual: rateio linear de jan a dez).'],
         size=9, color=TXT)
eb = shp(s5, 'Eyebrow'); _rs = eb.text_frame.paragraphs[0].runs
_rs[1].text = f'   |   {PROJ} · 12 SIGCOs'
for _r in _rs[2:]: _r._r.getparent().remove(_r._r)
clean_guidance(s5)
# rodapé: copia do slide de premissas
rod = copy.deepcopy(shp(S_[5], 'Rodapé')._element); s5.shapes._spTree.append(rod)
footer(s5, 4)

# =============================================================== Slide 6 — Premissas / Restrições / Penalidades
s6 = S_[5]
for i, t in enumerate(prem, 1):
    set_text(shp(s6, f'Premissa {i}'), t)
set_paras(shp(s6, 'Restrições lista'), restr)
eyebrow(s6); footer(s6, 5)
clean_guidance(s6)

# =============================================================== Slide 8 — Riscos
s8 = S_[7]
risks = [
 ('Acidente de trabalho', 'Acidente de trabalho durante a instalação dos equipamentos',
  ['Reunião de integração e alinhamento com a empreiteira', 'Inspeções de segurança periódicas', 'Realização do DDS'],
  ['Paralisar qualquer atividade executada de forma insegura', 'Acionar o SESMT', 'Investigar o ocorrido']),
 ('Atraso na aprovação de LSS / documentos', 'Atraso na aprovação das LSS e da documentação de terceiros pelo SESMT ETO',
  ['Antecipar o envio da documentação dos colaboradores', 'Acompanhar o prazo de 10 dias de análise'],
  ['Antecipar outras atividades da obra', 'Acompanhar as entregas junto ao SESMT']),
 ('Atraso de materiais e equipamentos', 'Entrega de RL/RT fora das datas da WBS (lead time de fornecimento a validar)',
  ['Antecipar a emissão dos PMAs e diligenciar fornecedores', 'Acompanhamento do forecast financeiro'],
  ['Priorizar as frentes pela meta de energização', 'Avaliar fornecedor homologado alternativo']),
 ('Indisponibilidade de Linha Viva / frentes simultâneas', 'Falta de equipe de Linha Viva ETO e até 6 frentes simultâneas (20/04 a 20/05/2027)',
  ['Programar as atividades com antecedência junto à ETO', 'Escalonar as frentes por meta de energização'],
  ['Reprogramar desligamentos e ajustar a sequência das atividades']),
 ('Atraso no comissionamento', 'Atraso no comissionamento e no ajuste de proteção dos RL/RT',
  ['Reunião semanal de acompanhamento da programação de comissionamento (DMSL/DEOP)'],
  ['Reavaliar a programação e adequar para finalizar os equipamentos no prazo']),
 ('Abandono de contrato', 'Indisponibilidade da empreiteira executora',
  ['Abertura de RFP'],
  ['Remanejamento de equipes entre regionais e aditivo de contratos vigentes']),
]
for i, (tt, dd, mit, cont) in enumerate(risks, 1):
    t = shp(s8, f'Risco {i} – título')
    set_runs(t.text_frame.paragraphs[0], tt); set_runs(t.text_frame.paragraphs[1], dd)
    pl = [s for s in s8.shapes if s.name == f'Risco {i} – plano']
    pl.sort(key=lambda s: s.left)
    set_paras(pl[0], mit); set_paras(pl[1], cont)
eyebrow(s8); footer(s8, 6)
clean_guidance(s8)

# =============================================================== Novos slides a partir do quadro do slide 10
def new_slide_like(base, title):
    sl = prs.slides.add_slide(base.slide_layout)
    for ph in list(sl.placeholders): drop(ph)
    for name in ('Title 2', 'Eyebrow', 'Rodapé'):
        el = copy.deepcopy(shp(base, name)._element); sl.shapes._spTree.append(el)
    set_text(shp(sl, 'Title 2'), title)
    return sl

s10 = S_[9]
# ---- WBS (EAP)
sw = new_slide_like(s10, 'WBS – EAP do Projeto (PMBOK)')
eyebrow(sw); footer(sw, 7)
def box(sl, x, y, w, h, fill, title, lines=None, tsize=11, lsize=9, tcolor='FFFFFF', lcolor=TXT, line=None):
    add_rect(sl, x, y, w, h, fill, line, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.06
    add_text(sl, x + 120000, y + 55000, w - 240000, 300000, title, tsize, True, tcolor, 'l', 'm')
    if lines: add_text(sl, x + 120000, y + 400000, w - 240000, h - 450000, lines, lsize, False, lcolor, 'l', 't')
X0, W0 = 457200, 11277295
# raiz
cx = X0 + W0 / 2
add_rect(sw, cx - 3300000, 1250000, 6600000, 400000, NAVY, None, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.15
add_text(sw, cx - 3300000, 1250000, 6600000, 400000, '1  PN 2027 – Instalação de Equipamentos Especiais (RL e RT)', 12, True, 'FFFFFF', 'c', 'm')
c0, c1, c2 = X0 + 1400000, X0 + 4350000, X0 + 5900000 + (W0 - 5900000) / 2
add_rect(sw, cx - 6000, 1650000, 12000, 170000, GREY)
add_rect(sw, c0, 1815000, c2 - c0, 12000, GREY)
for xx in (c0, c1, c2): add_rect(sw, xx - 6000, 1815000, 12000, 195000, GREY)
cols = [(X0, 2800000, TEAL), (X0 + 2950000, 2800000, ORANGE), (X0 + 5900000, W0 - 5900000, GREEN)]
y2 = 2010000; h2 = 3900000
box(sw, cols[0][0], y2, cols[0][1], h2, 'F3F5F8', '1.1  Gerenciamento do Projeto',
    ['1.1.1  Transfer Meeting (06/10/2026)', '1.1.2  Kickoff Meeting (29/10/2026)', '1.1.3  PRM – linha de base (02/12/2026)',
     '1.1.4  Monitoramento e controle: FUM mensal, reports, forecast, riscos', '1.1.5  Encerramento: CM, termo de aceite e lições aprendidas'], 11, 10.5, NAVY)
box(sw, cols[1][0], y2, cols[1][1], h2, 'F3F5F8', '1.2  Aquisições e Contratações',
    [f'1.2.1  RT ({n_rt}), RL ({n_rl}) e TripSaver (3) – PMA/RFP', '1.2.2  Materiais complementares', '1.2.3  Contratação da empreiteira executora (EPS) e O.S.',
     f'Data necessária em campo: {d8(S_min)} (1ª frente)'], 11, 10.5, NAVY)
eq_rows = [['Equipamento', '34,5 kV', '13,8 kV'], ['Regulador de tensão (RT)', '8', '1'], ['Religador (RL) novo', '9', '3'], ['Religador remanejado', '–', '1'], ['TripSaver', '3', '–']]
rebuild_table(sw, src, cols[1][0] + 120000, y2 + 2450000, [1500000, 580000, 580000], eq_rows, 255000, 8.5, 8.5, ['l', 'c', 'c'], False, name='Tabela equipamentos')
box(sw, cols[2][0], y2, cols[2][1], h2, 'F3F5F8', '1.3  Instalação, comissionamento e encerramento – 12 pacotes (1.3.1 a 1.3.12, um por SIGCO)', None, 11, 9.5, NAVY)
for _t in sw.shapes:
    if _t.has_text_frame and _t.text_frame.text.startswith(('1.1.1', '1.2.1')):
        for _p in _t.text_frame.paragraphs: _p.space_after = Pt(5)
# bloco das 10 atividades dentro do 1.3
tasks = [('1.3.n.1', 'Executar Obras', '30 / 45 d'), ('1.3.n.2', 'Obras Concluídas', 'marco'), ('1.3.n.3', 'Fiscalização', '12 d'),
         ('1.3.n.4', 'Cadastro EO / Integração parcial', '10 d'), ('1.3.n.5', 'Entrega do TCI / Integração final', '15 d'),
         ('1.3.n.6', 'Abertura de chamado / Atendimento GAT', '8 d'), ('1.3.n.7', 'Comissionar Equipamentos', '15 d'),
         ('1.3.n.8', 'Equipamentos em Operação', 'marco'), ('1.3.n.9', 'Encerramento Técnico', '7 d úteis'), ('1.3.n.10', 'Encerramento Contábil', '3 d úteis')]
tx = cols[2][0] + 120000; ty = y2 + 500000
tbl_rows = [['Código', 'Atividade / marco', 'Prazo']] + [list(t) for t in tasks]
rebuild_table(sw, src, tx, ty, [800000, 3300000, 1000000], tbl_rows, 255000, 9, 9, ['l', 'l', 'c'], True, name='Tabela EAP')
add_text(sw, tx, ty + 255000 * 11 + 70000, cols[2][1] - 240000, 500000,
         'Pacote P30 (até 4 equipamentos): execução em 30 dias · Pacote P45 (5 ou mais, SIGCO 90811): 45 dias. Prazos do histórico PN 2026 de RL/RT; dias corridos, exceto encerramentos (dias úteis).',
         8.5, False, GREY)
add_text(sw, X0, 6000000, W0, 330000, 'EAP em 3 níveis de entrega (regra dos 100%) · detalhamento completo, com responsáveis e predecessoras, na planilha WBS_Cronograma_PN2027.xlsx (aba WBS).',
         9, False, GREY, italic=True)

# ---- Base de planejamento dos prazos
sb = new_slide_like(s10, 'Base dos Prazos – PN 2026 (RL e RT)')
eyebrow(sb); footer(sb, 8)
ref = [['Bloco PN 2026 (WBS)', 'Equip.', 'Execução', 'Total'],
       ['BLOCO 1 – 5 RL + 1 remanej. (71018)', '6', '45 d', '101 d'],
       ['BLOCO 3 – 5 RL 13,8 kV (73521)', '5', '45 d', '101 d'],
       ['RT 34,5 kV Bielândia – Palmeirante (72240)', '1', '30 d', '86 d'],
       ['RT 34,5 kV Araguaína – Araguanã (71579)', '1', '30 d', '86 d'],
       ['AL SE Bielândia – RL (1) + RL (2) + RT (1) (71139)', '4', '30 d', '87 d'],
       ['Remanej. RT Paranã – Palmeirópolis (72938)', '1', '30 d', '87 d'],
       ['Remanej. RL 13,8 kV Palmeirópolis (81319)', '1', '30 d', '87 d']]
add_text(sb, 457200, 1215000, 6300000, 300000, 'Blocos de instalação de RL e RT usados como referência', 12, True, NAVY)
rebuild_table(sb, src, 457200, 1560000, [3900000, 700000, 900000, 800000], ref, 300000, 9, 9, ['l', 'c', 'c', 'c'], False, name='Tabela base 2026')
add_text(sb, 457200, 1560000 + 300000 * len(ref) + 120000, 6300000, 900000,
         ['Não foram usados prazos de planejamento (PMA, projeto executivo), obras de construção/recapacitação de rede nem bancos de capacitores.',
          'Regra: pacote com até 4 equipamentos → 30 dias de execução; 5 ou mais → 45 dias.'], 9.5, False, TXT)
add_text(sb, 7300000, 1215000, 4400000, 300000, 'Etapas comuns e encadeamento', 12, True, NAVY)
rule = [['Etapa', 'Prazo', 'Início'],
        ['Fiscalização', '12 d', 'após Obras Concluídas'],
        ['Cadastro EO / Integração parcial', '10 d', 'após Fiscalização'],
        ['Entrega do TCI / Integração final', '15 d', 'após Cadastro EO'],
        ['Abertura de chamado / GAT', '8 d', 'junto ao TCI'],
        ['Comissionar Equipamentos', '15 d', 'junto ao TCI'],
        ['Equipamentos em Operação', 'marco', 'fim do comissionamento'],
        ['Encerramento Técnico', '7 d úteis', 'após operação'],
        ['Encerramento Contábil', '3 d úteis', 'após Enc. Técnico']]
rebuild_table(sb, src, 7300000, 1560000, [2200000, 800000, 1434000], rule, 300000, 9, 9, ['l', 'c', 'l'], False, name='Tabela etapas')
add_rect(sb, 7300000, 1560000 + 300000 * len(rule) + 160000, 4434000, 1000000, 'F3F5F8', None, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
add_text(sb, 7420000, 1560000 + 300000 * len(rule) + 230000, 4200000, 900000,
         ['Método de datas: o início da execução de cada SIGCO é calculado de trás para frente, para que os equipamentos entrem em operação até o último dia do mês-meta de energização (TM 06/10/2026). '
          'Sem folga adotada: validar contra o lead time de fornecimento.'], 9, False, NAVY)

# ---- Cronograma macro (slide 9 do template)
s9 = S_[8]
eyebrow(s9); footer(s9, 9)
clean_guidance(s9)
gx0, gx1 = 3350000, 10500000           # eixo do tempo
t0, t1 = date(2027, 2, 1), date(2027, 12, 1)
def X(d): return gx0 + (gx1 - gx0) * (d - t0).days / (t1 - t0).days
y0 = 1250000; rh = 330000
# cabeçalho de meses
add_rect(s9, 457200, y0, 11277295, 280000, NAVY)
add_text(s9, 520000, y0, 800000, 280000, 'SIGCO', 9, True, 'FFFFFF', 'l', 'm')
add_text(s9, 1250000, y0, 2000000, 280000, 'Projeto', 9, True, 'FFFFFF', 'l', 'm')
mn = ['Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov']
for i, m in enumerate(mn):
    d0 = date(2027, 2 + i, 1)
    add_text(s9, X(d0), y0, X(date(2027, 3 + i, 1)) - X(d0), 280000, m + '/27', 8.5, True, 'FFFFFF', 'c', 'm')
add_text(s9, 10560000, y0, 1170000, 280000, 'Operação · Enc. contábil', 7.5, True, 'FFFFFF', 'c', 'm')
yb = y0 + 280000
for i, p in enumerate(P):
    y = yb + i * rh
    if i % 2 == 0: add_rect(s9, 457200, y, 11277295, rh, 'F3F5F8')
    r = p['sched']
    add_text(s9, 520000, y, 700000, rh, str(p['sigco']), 8.5, True, NAVY, 'l', 'm')
    add_text(s9, 1250000, y, 2050000, rh, p['ab'], 8, False, TXT, 'l', 'm')
    bh = 150000; by = y + (rh - bh) / 2
    segs = [(p['S'], r['exec'][1], NAVY), (r['fisc'][0], r['cad'][1], TEAL), (r['tci'][0], r['com'][1], GREEN), (r['et'][0], r['ec'][1], ORANGE)]
    for a_, b_, col in segs:
        add_rect(s9, X(a_), by, max(X(b_) - X(a_), 20000), bh, col)
    dm = add_rect(s9, X(r['op']) - 55000, y + (rh - 110000) / 2, 110000, 110000, 'C00000', 'FFFFFF', MSO_SHAPE.DIAMOND, 0.75)
    add_text(s9, 10560000, y, 1170000, rh, f"{d5(r['op'])} · {d5(r['ec'][1])}", 8, False, TXT, 'c', 'm')
yend = yb + len(P) * rh
# limite contábil
lx = X(date(2027, 11, 17))
ln = add_rect(s9, lx - 7000, y0 + 280000, 14000, yend - y0 - 280000, 'C00000')
add_text(s9, lx - 700000, yend + 20000, 1400000, 200000, 'Limite contábil 17/11/2027', 7.5, True, 'C00000', 'c')
# legenda
lgx = 457200; lgy = yend + 330000
items = [(NAVY, 'Execução (instalação)'), (TEAL, 'Fiscalização + Cadastro EO'), (GREEN, 'TCI / GAT / Comissionamento'), (ORANGE, 'Enc. Técnico + Contábil')]
for i, (c_, t_) in enumerate(items):
    add_rect(s9, lgx + i * 2400000, lgy + 40000, 220000, 120000, c_)
    add_text(s9, lgx + i * 2400000 + 270000, lgy, 2100000, 200000, t_, 8.5, False, TXT, 'l', 'm')
add_rect(s9, lgx + 9650000 + 0, lgy + 30000, 120000, 120000, 'C00000', None, MSO_SHAPE.DIAMOND)
add_text(s9, lgx + 9650000 + 170000, lgy, 1500000, 200000, 'Equip. em operação', 8.5, False, TXT, 'l', 'm')
add_text(s9, 457200, lgy + 270000, 11277295, 300000,
         f'{len(P)} SIGCOs · {n_rt} RT, {n_rl} RL e 3 TripSavers · primeira execução em {d8(S_min)}, última energização em {d8(op_max)}, encerramento contábil até {d8(ec_max)} (limite 17/11/2027).',
         9, False, GREY, italic=True)

# ---- Cronograma detalhado (slide 10 do template)
eyebrow(s10); footer(s10, 10)
clean_guidance(s10)
hdr = ['SIGCO / Projeto', 'Execução\n30/45 d', 'Fiscalização\n12 d', 'Cadastro EO\n10 d', 'TCI / Integração\n15 d', 'GAT\n8 d', 'Comissionamento\n15 d', 'Em operação\n(marco)', 'Enc. Técnico\n7 d úteis', 'Enc. Contábil\n3 d úteis']
rows = [hdr]
for p in P:
    r = p['sched']
    rg = lambda k_: f'{d5(r[k_][0])} a {d5(r[k_][1])}'
    rows.append([f"{p['sigco']} – {p['ab']}", rg('exec'), rg('fisc'), rg('cad'), rg('tci'), rg('gat'), rg('com'), d8(r['op']), rg('et'), rg('ec')])
colw = [2500000] + [975000] * 9
rebuild_table(s10, src, 457200, 1215000, colw, rows, 300000, 7.5, 7.5, ['l'] + ['c'] * 9, True, name='Tabela cronograma detalhado')
# cabeçalho em duas linhas: ajusta as células do cabeçalho
fr10 = [s for s in s10.shapes if s.name == 'Tabela cronograma detalhado'][0]
add_text(s10, 457200, 1215000 + 300000 * len(rows) + 100000, 11277295, 500000,
         ['Datas dd/mm de 2027 (marco de operação: dd/mm/aa). Execução: 30 dias (pacotes até 4 equipamentos) ou 45 dias (SIGCO 90811). Prazos do histórico PN 2026 de RL/RT.',
          'Início da execução calculado de trás para frente a partir do mês-meta de energização (TM 06/10/2026); encerramento contábil dentro do limite de 17/11/2027.'],
         8.5, False, GREY, italic=True)

# =============================================================== Slide 12 — Obrigado
s12 = S_[11]
for s in s12.shapes:
    if s.name == 'Eyebrow':
        rs = s.text_frame.paragraphs[0].runs
        rs[-1].text = f'  ·  {PROJ}' if len(rs) > 1 else rs[-1].text
        if len(rs) == 1: rs[0].text = f'KICKOFF MEETING  ·  {PROJ}'
    if s.name == 'Contato GERENTE DO PROJETO': set_runs(s.text_frame.paragraphs[1], GP)
clean_guidance(s12)

# =============================================================== Ordenar / remover slides
def remove_slide(prs, slide):
    sldIdLst = prs.slides._sldIdLst
    for sid in list(sldIdLst):
        if prs.part.related_part(sid.rId) is slide.part:
            prs.part.drop_rel(sid.rId); sldIdLst.remove(sid); return
for sl in (S_[3], S_[6], S_[10]): remove_slide(prs, sl)
new = [s for s in prs.slides if s not in (S_[0], S_[1], S_[2], S_[4], S_[5], S_[7], S_[8], S_[9], S_[11])]   # sw, sb
order = [S_[0], S_[1], S_[2], S_[4], S_[5], S_[7], sw, sb, S_[8], S_[9], S_[11]]
lst = prs.slides._sldIdLst
ids = {prs.part.related_part(s.rId): s for s in lst}
for s in list(lst): lst.remove(s)
for sl in order: lst.append(ids[sl.part])
prs.save(OUT)
print('saved', OUT, len(prs.slides.__iter__.__self__._sldIdLst))
