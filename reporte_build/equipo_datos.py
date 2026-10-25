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
# ---- Bandeja "Mis tareas" (maqueta: los botones no ejecutan nada todavía) ----
def nombre_corto(n):
    p = (n or '').split()
    w = p[0] if p else ''
    if len(w) < 3 or not w.isalpha() or (w.isupper() and len(p) == 1):
        return ''
    return w.capitalize()
def borrador(r):
    n = nombre_corto(r.get('nombre'))
    n = n if n else ''
    s = lambda t: t.replace('Hola , ', 'Hola, ')
    if r.get('etapa') == 'SEG POST VISITA':
        return s(f"Hola {n}, ¿cómo estás? Soy Carolina de M2100. Quería saber cómo te quedó la visita y si pudiste revisar "
                f"la información. Si te sirve, coordinamos una llamada corta para resolver dudas. ¡Quedo atenta!")
    if r.get('temperatura') == 'CALIENTE':
        return s(f"Hola {n}, ¿cómo estás? Te escribo de M2100 para retomar lo que conversamos. ¿Te acomoda coordinar "
                f"una nueva visita o prefieres que te envíe la cotización actualizada con la rebaja de IVA?")
    return s(f"Hola {n}, ¿cómo estás? Soy Carolina de M2100. Te escribo porque quedan pocas unidades con la rebaja de IVA "
            f"y me acordé de ti. ¿Te gustaría que te envíe las opciones disponibles?")
tareas = []
if sco:
    rk = sco.get('ranking') or []
    sel = [r for r in rk if r.get('temperatura') == 'CALIENTE']
    sel += [r for r in rk if r.get('temperatura') == 'TIBIO' and r.get('etapa') == 'SEG POST VISITA'][:4]
    sel += [r for r in rk if r.get('temperatura') == 'TIBIO' and r.get('etapa') != 'SEG POST VISITA'][:3]
    for i, r in enumerate(sel):
        tipo = ('Contactar hoy · lead caliente' if r.get('temperatura') == 'CALIENTE'
                else 'Aprobar seguimiento post visita' if r.get('etapa') == 'SEG POST VISITA' else 'Aprobar mensaje de reactivación')
        tareas.append({'id': f'sco{i}', 'agente': 'sco', 'prioridad': 'alta' if r.get('temperatura') == 'CALIENTE' else 'media',
                       'titulo': tipo, 'lead': r.get('nombre'), 'score': r.get('score'), 'temperatura': r.get('temperatura'),
                       'etapa': r.get('etapa'), 'ultimo': r.get('ultimo_cliente_iso') or r.get('ultimo_msg_iso'),
                       'dias': r.get('dias_sin_cliente'), 'racional': r.get('antecedentes'), 'senales': (r.get('senales') or [])[:3],
                       'siguiente': r.get('siguiente_paso'), 'mensaje': borrador(r),
                       'acciones': ['Aprobar y enviar WhatsApp', 'Mover a SEG POST VISITA' if r.get('etapa') == 'VISITA' else 'Agendar recordatorio', 'Descartar'],
                       'aprueba': 'Gianfranco', 'ejecuta': 'Carolina'})
if aud and aud.get('rojos'):
    tareas.append({'id': 'aud0', 'agente': 'aud', 'prioridad': 'alta', 'titulo': f"{aud['rojos']} leads esperan respuesta",
                   'racional': f"La auditoría de hoy detectó {aud['rojos']} conversaciones donde le debemos algo al cliente "
                               f"({aud.get('rojos_nuevos', 0)} nueva{'' if aud.get('rojos_nuevos', 0) == 1 else 's'} hoy). Carolina ya recibió el detalle por correo.",
                   'acciones': ['Confirmar que Carolina las atiende hoy', 'Ver lista'], 'aprueba': 'Gianfranco', 'ejecuta': 'Carolina'})
tareas.append({'id': 'rep0', 'agente': 'rep', 'prioridad': 'media', 'titulo': 'Revisar el análisis del Experto IA',
               'racional': 'El reporte nocturno dejó 5 recomendaciones sobre pauta y embudo de los últimos 30 días. Define cuáles se ejecutan esta semana.',
               'acciones': ['Ir a Performance', 'Asignar al equipo'], 'aprueba': 'Gianfranco', 'ejecuta': 'Equipo de marketing'})
cat['tareas'] = tareas
cat['actualizado'] = max(cortes) if cortes else cat.get('actualizado')
cat['avisos'] = avisos
print(json.dumps(cat, ensure_ascii=False, indent=1))
