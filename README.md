# Pipeline de Automatización Hidrológica para QGIS

Este complemento automatiza un flujo de trabajo hidrológico estructurado en 9 etapas
consecutivas dentro del entorno QGIS. Diseñado para el análisis geomorfológico y la
planificación territorial, el sistema procesa Modelos Digitales de Elevación (MDE)
mediante la integración de herramientas avanzadas de teledetección y algoritmos de
análisis espacial.

## Características Principales

- **Procesamiento en 9 Pasos:** Desde la corrección de depresiones en el MDE hasta
  la extracción de redes de drenaje e índices morfométricos avanzados.
- **Interoperabilidad de Motores:** Integración nativa de la API de QGIS, abstracción
  de datos raster/vectorial mediante GDAL y ejecución de algoritmos de alto rendimiento
  con Whitebox Workflows.
- **Gestión Avanzada de Datos:** Control automatizado de CRS, validación topológica de
  geometrías y optimización de memoria mediante archivos temporales.
- **Ámbito de Desarrollo:** Desarrollado en la Escuela de Geografía de la Universidad
  Austral de Chile (UACh).

---

## Descargas

[![Descargar script](https://img.shields.io/badge/⬇️%20Descargar-super_cuencas-blue?style=for-the-badge)](https://github.com/Luk343/super-cuencas/raw/main/herramienta_cuencas.py)

[![Descargar complemento completo](https://img.shields.io/badge/⬇️%20Descargar-Complemento%20completo%20(.zip)-green?style=for-the-badge)](https://github.com/Luk343/super-cuencas/archive/refs/heads/main.zip)

---

## Guía de Usuario — Super Cuencas

### Descripción

**Super Cuencas** es una herramienta de la Caja de Herramientas de QGIS que delimita
cuencas hidrográficas a partir de un DEM y una capa de exutorios, y calcula
automáticamente tres índices morfométricos por cuenca:

| Índice | Fórmula | Descripción |
|---|---|---|
| Índice de compacidad (Kc) | `Kc = 0.28 × P / √A` | Forma de la cuenca respecto a un círculo |
| Razón del relieve (Rr) | `Rr = (Hmax − Hmin) / Lcauce` | Pendiente media del cauce principal (m/km) |
| Densidad de drenaje (Dd) | `Dd = Lt / A` | Longitud total de cauces por unidad de área |

Además genera un perfil topográfico longitudinal (PNG) por cada cuenca.

---

### Requisitos previos

- QGIS 3.x (probado en 3.44.11)
- Complemento **Whitebox Workflows for QGIS** instalado y activado
  *(Complementos → Administrar e instalar complementos → Whitebox Workflows)*
- Un DEM en formato raster (GeoTIFF recomendado), preferentemente con CRS proyectado
  (metros). Se puede usar un DEM en grados geográficos activando la opción de
  reproyección.
- Una capa vectorial de **puntos de exutorios** (mínimo 2), uno por cuenca a delimitar.
- Python con `matplotlib` disponible en el entorno de QGIS (necesario para los perfiles
  topográficos).

---

### Instalación

#### Opción A — Método rápido (recomendado)

1. Descarga `super_cuencas_supremo.py` con el botón de arriba.
2. Abre la **Caja de Herramientas de Procesos** en QGIS.
3. En la barra superior de la Caja de Herramientas, haz clic en el ícono con el
   **logo de Python** 🐍.
4. Selecciona **"Agregar script a la caja de herramientas..."**
5. Navega hasta el archivo descargado y selecciónalo.
6. La herramienta aparecerá de inmediato bajo el grupo **Hidrología Avanzada**.

#### Opción B — Instalación manual

1. Descarga `super_cuencas_supremo.py`.
2. Cópialo manualmente en la carpeta de scripts de QGIS según tu sistema operativo:

| Sistema | Ruta |
|---|---|
| Windows | `%APPDATA%\QGIS\QGIS3\profiles\default\processing\scripts\` |
| macOS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/` |
| Linux | `~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts/` |

3. En la Caja de Herramientas: ícono Python 🐍 → **Recargar scripts**.
4. La herramienta aparecerá bajo el grupo **Hidrología Avanzada**.

---
### Pipeline interno (9 pasos)
---

### Parámetros de entrada

| Parámetro | Tipo | Descripción | Valor recomendado |
|---|---|---|---|
| DEM | Raster | Modelo Digital de Elevación | Cualquier CRS; preferir proyectado |
| Exutorios | Vectorial (puntos) | Puntos de salida de cada cuenca | Mínimo 2 puntos |
| Campo identificador | Campo de texto | Nombre de cada cuenca en la tabla de atributos | Dejar vacío → punto_0, punto_1… |
| Umbral de acumulación | Entero | Celdas mínimas para definir un cauce | 500–2000 (cuencas pequeñas); 2000–5000 (cuencas grandes) |
| Distancia snap (m) | Decimal | Radio para mover el exutorio al cauce más cercano | 50–200 m |
| Reproyección | Enum | Qué capas reproyectar al CRS de trabajo | *DEM y exutorios* si el DEM está en grados |
| Método de snap | Enum | Corrección de posición de exutorios | *Jenson Snap* (recomendado) |
| Modo de salida | Enum | Capas unificadas, separadas o ambas | *Solo unificado* por defecto |
| Punto de detención | Enum | Hasta qué paso ejecutar | 0 = proceso completo |
| Carpeta de salida | Carpeta | Dónde guardar los resultados | Carpeta vacía dedicada |

---

### Salidas

| Archivo | Formato | Descripción |
|---|---|---|
| `Cuencas_morfometria.shp` | Shapefile | Polígonos de cuencas con campos: `cuenca_id`, `Area_km2`, `Perim_km`, `Kc`, `H_max_m`, `H_min_m`, `Lcauce_km`, `Rr`, `Lt_km`, `Dd` |
| `Longest_Flowpath_todas.shp` | Shapefile | Cauce más largo de cada cuenca (unificado) |
| `Streams_Vector.shp` | Shapefile | Red de drenaje vectorial completa |
| `Puntos_Corregidos.shp` | Shapefile | Posición original y corregida de cada exutorio |
| `Cuencas_[ID].shp` | Shapefile | Polígono individual por cuenca (modo separado) |
| `Longest_Flowpath_[ID].shp` | Shapefile | Cauce más largo individual (modo separado) |
| `Perfil_topografico_[ID].png` | PNG (180 dpi) | Perfil longitudinal del cauce principal con Hmax, Hmin, desnivel, pendiente y Rr |

---

### Solución de problemas frecuentes

**La herramienta no aparece en la Caja de Herramientas**
→ Verifica que el archivo está en la carpeta correcta y recarga los scripts
(ícono Python 🐍 → Recargar scripts).

**Error: Whitebox Workflows no disponible**
→ Activa el complemento en *Complementos → Administrar complementos → Whitebox Workflows*.

**Los perfiles PNG no se generan**
→ `matplotlib` no está disponible en tu entorno de QGIS. En Windows instálalo desde
la consola de QGIS con `import subprocess; subprocess.run(["pip", "install", "matplotlib"])`.

**H_max / H_min aparecen como NULL en la tabla de atributos**
→ Verifica que el DEM cubre completamente el área de las cuencas delimitadas.

---

## Nota sobre nomenclatura

El nombre oficial de la herramienta es **Super Cuencas**, tal como aparece en la
Caja de Herramientas de QGIS (`displayName`). El archivo fuente del proyecto se
llama `super_cuencas_supremo.py`.

Para efectos de la entrega y evaluación del Práctico 6 del curso Aplicaciones SIG, 
el script se distribuye en este repositorio bajo el nombre `herramienta_cuencas.py`,
siguiendo el nombre de archivo solicitado en la pauta del práctico. Es exactamente
el mismo código; solo cambia el nombre del archivo en disco, no el nombre de la 
herramienta dentro de QGIS ni su funcionamiento.

---

## Licencia

Este proyecto está sujeto a los términos de la
[GNU General Public License v3.0 (GPL-3.0)](LICENSE).
Esto garantiza la libertad de usar, estudiar, compartir y modificar el software,
asegurando que cualquier trabajo derivado mantenga el código abierto.

