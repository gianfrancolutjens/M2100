"""Reorganiza el reporte de M2100 en 3 pestañas: Resumen ejecutivo, Performance y Scoring IA.
No toca la lógica de datos: solo envuelve los bloques existentes y agrega la pestaña Scoring.
Uso: python3 build_tabs.py reporte.html ultimo_scoring.json salida.html [equipo.json]
Idempotente: si el reporte ya tiene pestañas, solo actualiza los datos del scoring."""
import json, re, sys, os
rep, data, out = sys.argv[1:4]
base = os.path.dirname(os.path.abspath(__file__))
s = open(rep, encoding='utf-8').read()
leer = lambda n: open(os.path.join(base, n), encoding='utf-8').read()

try:
    d = json.load(open(data, encoding='utf-8'))
except Exception:
    d = None  # sin scoring: se conserva el bloque que ya estaba publicado
for r in (d or {}).get('ranking', []):
    r.pop('telefono', None); r.pop('email', None)
payload = json.dumps({k: d[k] for k in ('corte', 'conteo', 'umbrales', 'conteo_por_etapa', 'ranking') if k in (d or {})} or None,
                     ensure_ascii=False).replace('</', '<\\/')
scoring = leer('scoring_tab.html').replace('__SCORING_JSON__', payload).strip()
eq_path = os.path.join(base, 'equipo.json') if len(sys.argv) < 5 else sys.argv[4]
try:
    eq_data = json.load(open(eq_path, encoding='utf-8'))
except Exception:
    eq_data = None
eq_payload = json.dumps(eq_data, ensure_ascii=False).replace('</', '<\\/')
equipo = leer('equipo_tab.html').replace('__EQUIPO_JSON__', eq_payload).strip()

if '<!-- TABS:START -->' in s:
    if d is not None:
        s = re.sub(r'<!-- SCORING:START -->[\s\S]*?<!-- SCORING:END -->', lambda m: scoring, s)
    if '<!-- EQUIPO:START -->' in s:
        if eq_data is not None:
            s = re.sub(r'<!-- EQUIPO:START -->[\s\S]*?<!-- EQUIPO:END -->', lambda m: equipo, s)
    else:
        s = s.replace('<!-- SCORING:END -->', '<!-- SCORING:END -->\n' + equipo, 1)
    for blk, f in (('TABS', 'tabs.html'), ('PERIODO', 'periodo.html'), ('TABSJS', 'tabs_js.html')):
        if f'<!-- {blk}:START -->' in s:
            s = re.sub(rf'<!-- {blk}:START -->[\s\S]*?<!-- {blk}:END -->', lambda m, f=f: leer(f).strip(), s)
else:
    i = s.index('<div class="filter-bar"')
    s = s[:i] + leer('tabs.html') + '\n' + s[i:]
    blocks = [m.start() for m in re.finditer(r'<div class="section-block">', s)]
    assert len(blocks) >= 2, 'se esperaban al menos 2 section-block'
    assert 'Resumen por Fuente' in s[blocks[0]:blocks[1]], 'el primer bloque no es el Resumen por Fuente'
    k = s.index('<div class="footer">')
    s = (s[:blocks[0]] + '<div id="tab-resumen">\n' + s[blocks[0]:blocks[1]] + '</div>\n'
         + '<div id="tab-performance" style="display:none">\n' + s[blocks[1]:k] + '</div>\n'
         + scoring + '\n' + equipo + '\n' + s[k:])
    # Botón "Todo el período" en el filtro de fechas
    b90 = s.index('data-key="90d"'); fin = s.index('</button>', b90) + len('</button>')
    s = s[:fin] + '\n      <button class="filter-btn" data-key="all">Todo el per&iacute;odo</button>' + s[fin:]
    j = s.rindex('</body>')
    s = s[:j] + leer('periodo.html') + '\n' + leer('tabs_js.html') + '\n' + s[j:]
open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
