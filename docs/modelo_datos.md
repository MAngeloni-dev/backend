# Modelo de datos del CRM Veterinario

Documento de entidades, relaciones y reglas del backend. Complementa el [README](../README.md), donde se incluyen los diagramas Mermaid de los tres bloques del sistema.

Describe el modelo desarrollado durante el proyecto. No reemplaza el registro de la planificación inicial: las decisiones previas y las ampliaciones deben identificarse en el historial y tablero de trabajo.

## Entidades y campos principales

| Modelo | Campos principales | Relaciones obligatorias u opcionales |
| --- | --- | --- |
| Usuario | Campos de AbstractUser y `rol`; estados de acceso de Django. | Referenciado por operaciones clínicas, reservas y movimientos. |
| Tutor | `nombre`, `apellido`, `dni`, `telefono`, `email`, `direccion`, `observaciones`, `activo`, fechas. | Puede tener cero o muchos pacientes. |
| Especie | `nombre`, `activo`. | Puede tener razas, pacientes y asociaciones con medicamentos. |
| Raza | `nombre`, `activo`. | Especie obligatoria. |
| Paciente | `nombre`, `sexo`, `fecha_nacimiento`, `nacimiento_estimado`, `castrado`, `color`, `microchip`, `observaciones`, `activo`, fechas. | Tutor y especie obligatorios; raza opcional. |
| Consulta | Fecha, motivo, síntomas, diagnóstico, tratamiento, observaciones, peso opcional y fechas de registro. | Paciente y veterinario. |
| Turno | `inicio`, `fin`, `motivo`, `observaciones`, `estado`, fechas. | Paciente, veterinario y creador obligatorios. |
| Medicamento | `nombre`, `laboratorio`, `principio_activo`, `concentracion`, `presentacion`, `contenido_neto`, `unidad_contenido`, `codigo_barras`, `via_administracion`, `stock_minimo`, `observaciones`, `activo`, fechas. | Especies mediante relación muchos a muchos opcional. |
| Lote | `numero`, `fecha_vencimiento`, `cantidad_actual`, `observaciones`, `activo`, fechas. | Medicamento obligatorio. |
| MovimientoStock | `tipo`, `cantidad`, `cantidad_anterior`, `cantidad_posterior`, `motivo`, `observaciones`, `fecha_creacion`. | Lote y responsable obligatorios. |
| Internacion | `fecha_ingreso`, `fecha_egreso`, `motivo`, `diagnostico`, `observaciones`, `estado`, fechas de registro. | Paciente, veterinario y creador obligatorios. |
| EvolucionInternacion | `fecha`, `peso`, `temperatura`, `frecuencia_cardiaca`, `frecuencia_respiratoria`, `observaciones`, `indicaciones`, `fecha_creacion`. | Internación y profesional obligatorios. |

Las claves primarias se generan automáticamente. Los nombres exactos, tipos y restricciones vigentes se verifican en los modelos y migraciones del repositorio.

## Cardinalidades

`1:N` significa que una entidad puede relacionarse con muchos registros del otro lado. Cada registro hijo conserva una referencia a su padre. Un padre puede tener cero registros hijos.

| Relación | Cardinalidad | Interpretación |
| --- | --- | --- |
| Tutor → Paciente | 1:N | Cada paciente tiene un tutor responsable. |
| Especie → Raza | 1:N | Cada raza corresponde a una especie. |
| Especie → Paciente | 1:N | Cada paciente tiene una especie. |
| Raza → Paciente | 1:N, opcional en paciente | Puede haber pacientes sin raza registrada. |
| Paciente → Consulta | 1:N | Un paciente acumula atenciones clínicas. |
| Usuario → Consulta | 1:N | El profesional registra consultas. |
| Paciente → Turno | 1:N | Un paciente puede tener varias reservas históricas. |
| Usuario → Turno como veterinario | 1:N | Un profesional recibe reservas. |
| Usuario → Turno como creador | 1:N | Se identifica quién agendó. |
| Medicamento ↔ Especie | N:M | Varios medicamentos pueden asociarse con varias especies. |
| Medicamento → Lote | 1:N | Se separan las partidas y vencimientos. |
| Lote → MovimientoStock | 1:N | El historial modifica una partida concreta. |
| Usuario → MovimientoStock | 1:N | Cada movimiento tiene responsable. |
| Paciente → Internacion | 1:N | Puede tener distintas estadías; solo una abierta. |
| Usuario → Internacion como veterinario | 1:N | Profesional a cargo de la internación. |
| Usuario → Internacion como creador | 1:N | Cuenta que registró el ingreso. |
| Internacion → EvolucionInternacion | 1:N | Una estadía puede tener muchos controles. |
| Usuario → EvolucionInternacion | 1:N | Cada control identifica a su autor. |

No existe todavía una relación de aplicación de medicamentos entre lotes y pacientes o internaciones. Los retiros actuales registran un movimiento con motivo, no una administración clínica de dosis.

## Restricciones y decisiones

### Identidad y catálogos

- Usuario utiliza la infraestructura de autenticación de Django y un rol operativo propio.
- Los nombres de especie y la combinación raza-especie se controlaron para evitar duplicados sin distinguir mayúsculas.
- Los modelos con estado activo permiten baja lógica según sus permisos.
- Los datos de contacto del tutor no se duplican como campos del paciente: se obtienen mediante la relación.

### Pacientes y atención

- La raza debe pertenecer a la especie seleccionada.
- El nacimiento no puede ser futuro; si se declara estimado, debe existir una fecha.
- El microchip vacío se normaliza a null y el valor informado debe ser único.
- Consulta conserva el paciente y profesional de la atención. Los detalles clínicos tienen acceso restringido.

### Turnos

- `fin > inicio` está protegido mediante CheckConstraint.
- ExclusionConstraint impide intervalos superpuestos de un mismo veterinario para estados distintos de CANCELADO.
- El rango se interpreta con inicio incluido y fin excluido; permite turnos consecutivos.
- La extensión btree_gist debe instalarse antes de la restricción correspondiente.
- El modelo valida disponibilidad; el ViewSet controla estados y traduce conflictos de reserva a errores de API.

### Medicamentos y lotes

- El contenido neto debe ser positivo.
- Se controla la unicidad de la presentación comercial mediante nombre, laboratorio, concentración, presentación, contenido y unidad, con normalización de mayúsculas en los textos incluidos.
- El código de barras es opcional y único cuando está informado.
- El número de lote es único por medicamento sin distinguir mayúsculas.
- El lote conserva una fecha de vencimiento y cantidad no negativa.
- `cantidad_actual` no se edita desde los formularios ni la API ordinarios: se modifica mediante el servicio de movimientos.
- La relación medicamento-especies vacía significa sin especificar; no declara seguridad de uso en todas las especies.

### Movimientos y transacciones

La cantidad del movimiento es positiva. INGRESO y AJUSTE_ENTRADA suman; RETIRO y AJUSTE_SALIDA restan. La base controla coherencia entre cantidad anterior, cantidad movida y resultado.

El servicio `registrar_movimiento` valida al responsable, bloquea el lote con `select_for_update`, calcula el nuevo saldo, crea el historial y guarda la cantidad del lote dentro de `transaction.atomic`. No permite saldo negativo. Un error revierte la operación completa.

Los movimientos históricos no se editan ni borran por las interfaces implementadas. Una corrección es otro movimiento con motivo. Esto no significa que el ORM o la base sean inmutables ante cualquier intervención externa: las escrituras del sistema deben respetar sus servicios.

### Internación y evolución

- UniqueConstraint condicional impide más de una internación en estado INTERNADO por paciente.
- CheckConstraint relaciona estado y egreso: abierta sin egreso; ALTA o FALLECIDO con egreso no anterior al ingreso.
- El servicio exige paciente y tutor activos al abrir y un profesional activo con rol válido.
- Cada evolución conserva profesional, fecha y observaciones obligatorias; mediciones e indicaciones son opcionales según su campo.
- El control no puede ser futuro, anterior al ingreso o posterior al egreso.
- El cierre comprueba que el egreso no sea anterior a un control existente.
- Cierre y registro de evolución bloquean la misma internación para coordinar operaciones simultáneas.
- Después del cierre no se aceptan nuevas evoluciones mediante el servicio.
- El modelo actual no contiene un campo propio de usuario que cerró la internación. Cuando se cierra desde el panel se registra la operación en el historial administrativo de Django.

## Eliminación y conservación

Las relaciones históricas configuradas con `PROTECT` impiden borrar padres referenciados. Las bajas de catálogos se gestionan con `activo` donde corresponde. PROTECT no impide por sí mismo editar campos ni equivale a una auditoría completa.

## Evidencia de implementación

Desde la carpeta backend:

```powershell
docker compose exec backend python manage.py showmigrations
docker compose exec backend python manage.py check
```

Las migraciones aplicadas aparecen con `[X]`. Para inspeccionar una migración concreta puede usarse `sqlmigrate` con el nombre real de la app y de la migración. No regenerar migraciones únicamente para actualizar documentación.

## Evolución futura del modelo

La administración de dosis, comprobantes, archivos adjuntos y otras ampliaciones requieren diseño adicional. No deben representarse como relaciones existentes hasta implementar y migrar sus modelos.
