"""Actualiza los KPIs del organigrama (pestaña Equipo IA) con el estado real de los agentes.
Uso: python3 equipo_datos.py equipo.json ultima_auditoria.json ultimo_scoring.json > equipo_hoy.json
Si falta un archivo de estado, deja los valores del catálogo y lo anota en "avisos"."""
import json, sys
MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
def cargar(p):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return None
def fecha(iso):
    if not iso: return ''
    return f"{int(iso[8:10])} {MESES[int(iso[5:7]) - 1]} · {iso[11:16]}"
cat, aud, sco = cargar(sys.argv[1]), cargar(sys.argv[2]), cargar(sys.argv[3])
N = {n['id']: n for n in cat['nodos']}
avisos, cortes = [], []
def kpi(nid, i, v):
    if nid in N and i < len(N[nid].get('kpis', [])): N[nid]['kpis'][i]['v'] = str(v)
if aud:
    pe = aud.get('auditadas_por_etapa', {}); total = sum(pe.values())
    for i, v in enumerate([total, aud.get('rojos', 0), aud.get('rojos_nuevos', 0), aud.get('errores', 0)]): kpi('aud', i, v)
    kpi('com', 0, total); kpi('com', 1, aud.get('rojos', 0)); kpi('dir', 0, total)
    kpi('car', 0, aud.get('rojos', 0)); kpi('car', 1, pe.get('VISITA', 0) + pe.get('SEG POST VISITA', 0))
    ok = (aud.get('correo') or {}).get('ok')
    N['aud'].update(ultima=fecha(aud.get('corte')), resultado='ok' if ok else 'falla',
                    resultado_txt=(f"Correo enviado a {str((aud.get('correo') or {}).get('detalle', '')).count('@')} destinatarios"
                                   if ok else 'Correo NO enviado'))  # nunca publicar correos: el reporte es público
    cortes.append(aud.get('corte') or '')
else:
    avisos.append('sin estado de auditoría')
if sco:
    c = sco.get('conteo', {}); r = (sco.get('ranking') or [{}])[0]
    kpi('sco', 0, sum(c.values())); kpi('sco', 1, c.get('CALIENTE', 0)); kpi('sco', 2, c.get('TIBIO', 0))
    kpi('sco', 3, f"{r.get('nombre', '—')} · {r.get('score', '')}" if r else '—')
    kpi('dir', 1, c.get('CALIENTE', 0)); kpi('react', 0, c.get('TIBIO', 0))
    ok = (sco.get('correo') or {'ok': True}).get('ok', True)
    N['sco'].update(ultima=fecha(sco.get('corte')), resultado='ok' if ok else 'falla',
                    resultado_txt=('Corrida de prueba · ' if sco.get('prueba') else '') + ('Ranking enviado' if ok else 'Correo NO enviado'))
    cortes.append(sco.get('corte') or '')
else:
    avisos.append('sin estado de scoring')
if aud:
    pe = aud.get('auditadas_por_etapa', {}); kpi('post', 0, pe.get('VISITA', 0) + pe.get('SEG POST VISITA', 0))
cat['actualizado'] = max(cortes) if cortes else cat.get('actualizado')
cat['avisos'] = avisos
print(json.dumps(cat, ensure_ascii=False, indent=1))
