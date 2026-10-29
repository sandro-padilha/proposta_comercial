"""Motor de datas do PN 2027 (instalação de RL e RT) — replica a lógica dos blocos RL/RT do WBS PN 2026."""
from datetime import date, timedelta
import calendar

# Feriados nacionais 2026-2027 (sem Carnaval/ponto facultativo; o WBS 2026 também não os considerava)
HOLIDAYS = [date(2026,9,7),date(2026,10,12),date(2026,11,2),date(2026,11,15),date(2026,12,25),
            date(2027,1,1),date(2027,3,26),date(2027,4,21),date(2027,5,1),date(2027,5,27),
            date(2027,9,7),date(2027,10,12),date(2027,11,2),date(2027,11,15),date(2027,12,25)]

def is_bd(d, hol=HOLIDAYS):
    return d.weekday() < 5 and d not in hol

def workday(d, n, hol=HOLIDAYS):
    """Equivalente a WORKDAY(d; n; feriados) do Excel (n >= 0)."""
    step = 1 if n >= 0 else -1
    k = abs(n)
    while k:
        d += timedelta(days=step)
        if is_bd(d, hol): k -= 1
    return d

# Prazos (dias) — origem: blocos RL/RT do WBS PN 2026
PHASE_DAYS = dict(fisc=12, cad=10, tci=15, gat=8, com=15, et=7, ec=3)
EXEC_DAYS = {'P30': 30, 'P45': 45}   # P30: pacote até 4 equipamentos; P45: 5 ou mais (BLOCO 5 RL)

def forward(S, exec_days, hol=HOLIDAYS):
    r = {}
    r['exec'] = (S, S + timedelta(days=exec_days))
    r['conc'] = r['exec'][1]
    fs = workday(r['conc'], 1, hol); r['fisc'] = (fs, fs + timedelta(days=PHASE_DAYS['fisc']))
    cs = workday(r['fisc'][1], 1, hol); r['cad'] = (cs, cs + timedelta(days=PHASE_DAYS['cad']))
    ts = workday(r['cad'][1], 1, hol); r['tci'] = (ts, ts + timedelta(days=PHASE_DAYS['tci']))
    r['gat'] = (ts, ts + timedelta(days=PHASE_DAYS['gat']))
    r['com'] = (ts, ts + timedelta(days=PHASE_DAYS['com']))
    r['op'] = r['com'][1]
    es = workday(r['op'], 1, hol); r['et'] = (es, workday(es, PHASE_DAYS['et'], hol))
    ks = workday(r['et'][1], 1, hol); r['ec'] = (ks, workday(ks, PHASE_DAYS['ec'], hol))
    return r

def eom(y, m): return date(y, m, calendar.monthrange(y, m)[1])

def backward(meta_op, exec_days, hol=HOLIDAYS):
    """Último início de execução (dia útil) tal que 'Equipamentos em Operação' <= meta_op."""
    S = meta_op - timedelta(days=exec_days + 60)
    best = None
    for i in range(0, 200):
        d = S + timedelta(days=i)
        if not is_bd(d, hol): continue
        if forward(d, exec_days, hol)['op'] <= meta_op: best = d
        else: break
    return best

# ---------------- Carteira PN 2027 (12 SIGCOs) -----------------
# n: nº de equipamentos; pkg: P30/P45; meta: mês de energização (TM 06/10/2026 / Cadastro CAPEX)
PROJECTS = [
 dict(sigco=90811, ab='UHE Isamu – Ponte Alta', nome='Instalação de RL e RT - LD UHE Isamu - Ponte Alta - 1UI1 - QP', cap='Qualidade do Produto',
      eq='4 RL 34,5 kV + 3 RT 34,5 kV (+ 0,25 km RD MT e 2 chaves faca)', rl=4, rt=3, n=7, pkg='P45', meta=(2027,4), b_ago=1627896.9854, b_1010=1801604.82,
      ben='Tensão 0,91 → 0,95 pu'),
 dict(sigco=91979, ab='Gurupi – Duere', nome='Estudo de QS - LD Gurupi - Duere', cap='Qualidade do Serviço',
      eq='1 RL rural 34,5 kV + 3 TripSaver', rl=1, rt=0, n=4, pkg='P30', meta=(2027,5), b_ago=275195.3599, b_1010=239581.77,
      ben='DEC −0,557 h / FEC −0,104 (base conjunto)'),
 dict(sigco=92118, ab='4 de Araguaína IV', nome='Estudo de QS - 4 de Araguaína IV', cap='Qualidade do Serviço',
      eq='1 RL automático 13,8 kV', rl=1, rt=0, n=1, pkg='P30', meta=(2027,5), b_ago=121831.5199, b_1010=110736.26,
      ben='DEC −0,078 h / FEC −0,030 (base conjunto)'),
 dict(sigco=89267, ab='Xambioá II – Araguanã', nome='Instalação de RT - LD Xambioá II - Araguanã - 2XB2 - QP', cap='Qualidade do Produto',
      eq='2 RT 34,5 kV', rl=0, rt=2, n=2, pkg='P30', meta=(2027,5), b_ago=1083084.5918, b_1010=802322.332,
      ben='Tensão 0,929 → 0,945 pu'),
 dict(sigco=92094, ab='Palmas – Aparecida do Rio Negro', nome='Estudo de QS - LD Palmas - Aparecida do Rio Negro', cap='Qualidade do Serviço',
      eq='3 RL automáticos 34,5 kV', rl=3, rt=0, n=3, pkg='P30', meta=(2027,6), b_ago=505316.5797, b_1010=390750.03,
      ben='DEC −0,402 h / FEC −0,204 (base conjunto)'),
 dict(sigco=92095, ab='Palmas – Lajeado', nome='Estudo de QS - LD Palmas - Lajeado', cap='Qualidade do Serviço',
      eq='1 RL automático 34,5 kV', rl=1, rt=0, n=1, pkg='P30', meta=(2027,6), b_ago=168438.8599, b_1010=130250.01,
      ben='DEC −0,325 h / FEC −0,069 (base conjunto)'),
 dict(sigco=92101, ab='8 de Palmas IV', nome='Estudo de QS - 8 de Palmas IV', cap='Qualidade do Serviço',
      eq='1 RL automático 13,8 kV (N.A)', rl=1, rt=0, n=1, pkg='P30', meta=(2027,6), b_ago=121831.5199, b_1010=110736.26,
      ben='DEC −0,141 h / FEC −0,076 (base conjunto)'),
 dict(sigco=92102, ab='6 de Palmas IV', nome='Estudo de QS - 6 de Palmas IV', cap='Qualidade do Serviço',
      eq='1 RL automático 13,8 kV (N.F)', rl=1, rt=0, n=1, pkg='P30', meta=(2027,6), b_ago=121831.5199, b_1010=110736.26,
      ben='DEC −0,043 h / FEC −0,017 (base conjunto)'),
 dict(sigco=70838, ab='Cristalândia – Lagoa da Confusão', nome='Instalação de RT - LD Cristalândia - Lagoa da Confusão', cap='Qualidade do Produto',
      eq='1 RT 34,5 kV', rl=0, rt=1, n=1, pkg='P30', meta=(2027,6), b_ago=539995.5199, b_1010=399614.39,
      ben='Tensão 0,91 → 0,96 pu'),
 dict(sigco=70978, ab='Paraíso – Caseara', nome='Instalação de RT e Balanceamento de Fase - LD Paraíso I - Caseara - 2PR0 - QP', cap='Qualidade do Produto',
      eq='1 RT 34,5 kV + balanceamento de fase (3 ramais)', rl=0, rt=1, n=1, pkg='P30', meta=(2027,6), b_ago=540294.8959, b_1010=399913.766,
      ben='Tensão 0,91 → 0,97 pu'),
 dict(sigco=89249, ab='Araguaína – Babaçulândia', nome='Instalação de RT - LD Araguaína - Babaçulândia - 2AR0 - QP', cap='Qualidade do Produto',
      eq='1 RT 34,5 kV', rl=0, rt=1, n=1, pkg='P30', meta=(2027,8), b_ago=539995.5199, b_1010=399614.39,
      ben='Tensão 0,921 → 0,953 pu'),
 dict(sigco=89307, ab='1 de Figueirópolis', nome='Instalação de RT - 1 de Figueirópolis - 2FGR - QP', cap='Qualidade do Produto',
      eq='1 RT 13,8 kV + remanejamento de 1 RL 13,8 kV', rl=1, rt=1, n=2, pkg='P30', meta=(2027,8), b_ago=373175.8639, b_1010=330989.034,
      ben='Tensão 0,92 → 0,96 pu'),
]
MAT_PCT = 0.60   # parcela material (KOM 2026: R$15,48 mi material / R$25,79 mi total)

PHASES = [  # chave, nome (idêntico ao WBS 2026), dias-chave
 ('exec','Executar Obras'),('conc','Obras Concluídas'),('fisc','Fiscalização'),('cad','Cadastro EO/ Integração parcial'),
 ('tci','Entrega do TCI pela empreiteira / Integração final'),('gat','Abertura de chamado/ Atendimento GAT'),
 ('com','Comissionar Equipamentos'),('op','Equipamentos em Operação'),('et','Encerramento Técnico'),('ec','Encerramento Contábil')]

def build():
    out = []
    for p in PROJECTS:
        d = EXEC_DAYS[p['pkg']]
        meta = eom(*p['meta'])
        S = backward(meta, d)
        r = forward(S, d)
        q = dict(p); q.update(S=S, d=d, meta_dt=meta, sched=r)
        out.append(q)
    return out

if __name__ == '__main__':
    # Validação: reproduz blocos do PN 2026
    chk = [(date(2026,8,10),45,'2026-09-24','2026-11-03','2026-11-19'),   # BLOCO 1 (5 RL)
           (date(2026,7,7),30,'2026-08-06','2026-09-15','2026-10-01'),    # RT Bielândia-Palmeirante
           (date(2026,5,11),30,'2026-06-10','2026-07-21','2026-08-06'),   # remanej. RT Paranã-Palmeirópolis
           (date(2026,6,22),45,'2026-08-06','2026-09-15','2026-10-01')]   # BLOCO 3 (5 RL)
    for S,d,e,o,c in chk:
        r = forward(S,d,hol=[])
        print(S, d, r['exec'][1].isoformat()==e, r['op'].isoformat()==o, r['ec'][1].isoformat()==c, (r['ec'][1]-S).days)
    print()
    for q in build():
        r=q['sched']
        print(q['sigco'], q['S'], '->exec', r['exec'][1], 'op', r['op'], 'meta', q['meta_dt'], 'folga', (q['meta_dt']-r['op']).days, 'EC', r['ec'][1], 'dur', (r['ec'][1]-q['S']).days)
