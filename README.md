# Pipeline de Automatización Hidrológica para QGIS

<div align="center">

![Super Cuencas Logo](super_cuencas_logo.svg)

**Super Cuencas** — Delimitación y análisis automático de cuencas hidrográficas

</div>

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

[![Descargar script](https://img.shields.io/badge/⬇️%20Descargar-Script_super_cuencas-blue?style=for-the-badge)](https://github.com/Luk343/super-cuencas/raw/main/herramienta_cuencas.py)

[![Descargar complemento completo](https://img.shields.io/badge/⬇️%20Descargar-Complemento_(.zip)-green?style=for-the-badge)](https://github.com/Luk343/super-cuencas/archive/refs/heads/main.zip)

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
6. La herramienta aparece de inmediato bajo el grupo **Hidrología Avanzada**
   en la Caja de Herramientas de Procesos, sin necesidad de reiniciar QGIS.

#### Opción B — Instalación manual

1. Descarga `super_cuencas_supremo.py`.
2. Cópialo manualmente en la carpeta de scripts de QGIS según tu sistema operativo:

| Sistema | Ruta |
|---|---|
| Windows | `%APPDATA%\QGIS\QGIS3\profiles\default\processing\scripts\` |
| macOS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/` |
| Linux | `~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts/` |

3. **Cierra y vuelve a abrir QGIS.** La herramienta aparecerá bajo el grupo
   **Hidrología Avanzada** en la Caja de Herramientas de Procesos.

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

#### Problemas generales de la herramienta

**La herramienta no aparece en la Caja de Herramientas**
→ Si la agregaste con la Opción A, revisa que seleccionaste el archivo correcto en
*Agregar script a la caja de herramientas...*. Si la copiaste manualmente (Opción B),
verifica que está en la carpeta correcta y **cierra y vuelve a abrir QGIS** — esa opción
no se actualiza en caliente.

**Modifiqué el script y QGIS sigue ejecutando la versión vieja**
→ QGIS guarda una copia compilada en `__pycache__`, dentro de la misma carpeta de
scripts. Borra:

- el archivo `.py` que está en `processing/scripts/`
- la carpeta `processing/scripts/__pycache__` según tu SO:
  - **Windows:** `C:\Users\<usuario>\AppData\Roaming\QGIS\QGIS3\profiles\default\processing\scripts\__pycache__`
  - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__`
  - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__`

Luego vuelve a agregar el script nuevo con la **Opción A** o la **Opción B** y
cierra y vuelve a abrir QGIS para que tome los cambios.

**Los perfiles PNG no se generan**
→ `matplotlib` no está disponible en tu entorno de QGIS. Instálalo desde
la consola de QGIS (Complementos → Consola de Python):

```python
import subprocess
subprocess.run(["pip", "install", "matplotlib"])
```

**H_max / H_min aparecen como NULL en la tabla de atributos**
→ Verifica que el DEM cubre completamente el área de las cuencas delimitadas.

---

#### Problemas con Whitebox Workflows

**Error: "ModuleNotFoundError: No module named 'pip'" o "No module named 'ensurepip'"**
→ En Ubuntu/Debian/Pop!_OS, Whitebox necesita pip instalado en el sistema:

```bash
sudo apt install python3-pip
```

Si `dpkg` está roto (ves "se interrumpió la ejecución de dpkg"):

```bash
sudo dpkg --configure -a
sudo apt install python3-pip
```

Luego instala el backend de Whitebox:

```bash
pip3 install --user whitebox-workflows
```

**Whitebox deja de funcionar después de actualizar**
→ Las actualizaciones de Whitebox a veces dejan archivos antiguos/corruptos. La solución es
**limpiar completamente** la instalación anterior y dejar que QGIS la reinstale:

**Windows (CMD, con QGIS cerrado):**
```cmd
rmdir /s /q "C:\Users\AQUI_VA_TU_USUARIO\AppData\Roaming\QGIS\QGIS3\profiles\default\python\whitebox_workflows_lib"
```

Para saber tu usuario:
```cmd
echo %USERNAME%
```

**Linux (Terminal, con QGIS cerrado):**
```bash
rm -rf /home/AQUI_VA_TU_USUARIO/.local/share/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib
```

Para saber tu usuario:
```bash
whoami
```

**macOS (Terminal, con QGIS cerrado):**
```bash
rm -rf ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib
```

Después de ejecutar el comando según tu SO, **abre QGIS normalmente**. El plugin detectará
que falta el backend y lo reinstalará automáticamente. Esto resuelve ~95% de los problemas
de Whitebox después de actualizaciones.

**Error: "Whitebox Workflows no disponible"**
→ Activa el complemento en *Complementos → Administrar complementos → Whitebox Workflows* y reinicia QGIS.

---

### Compatibilidad con macOS

Super Cuencas funciona en **macOS 10.15+** con QGIS 3.x instalado. Las rutas de carpetas
difieren de Windows y Linux:

| Elemento | Ruta en macOS |
|---|---|
| Scripts de procesamiento | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/` |
| Caché de QGIS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__` |
| Backend de Whitebox | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib` |

**Requisitos adicionales en macOS:**
- Homebrew instalado (para `python3-pip` si es necesario)
- Whitebox se instala igual que en Linux: `pip3 install --user whitebox-workflows`

La mayoría de problemas comunes (Whitebox no disponible, perfiles PNG no generan) tienen
las mismas soluciones que en Windows/Linux, solo cambian las rutas de carpetas.

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

