# Pestañas del reporte M2100

La tarea nocturna "Reporte M2100" usa esta carpeta después de actualizar RAW, título, Generado e insights (PASO 5C).

```
python3 reporte_build/equipo_datos.py reporte_build/equipo.json /tmp/ultima_auditoria.json /tmp/ultimo_scoring.json > /tmp/equipo_hoy.json
python3 reporte_build/build_tabs.py index.html /tmp/ultimo_scoring.json index.html /tmp/equipo_hoy.json
```

- `ultima_auditoria.json` y `ultimo_scoring.json` vienen de `barrio-digital/barrio-ops` → `state/m2100/`.
- Si falta alguno de esos archivos, el builder conserva el bloque ya publicado (no rompe la página).
- Es idempotente: correrlo dos veces da el mismo archivo.
- El reporte es público: el ranking se publica solo con nombres (el builder borra teléfono y email).
- `equipo.json` es el catálogo del organigrama (cargos, descripción, herramientas). Los KPIs con `src` se leen en vivo de las tablas del Resumen ejecutivo y siguen el filtro de fechas.
