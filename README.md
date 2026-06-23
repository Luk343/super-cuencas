# 🌊 Super Cuencas

**Automatización hidrológica para QGIS** — Delimitación y análisis automático de cuencas hidrográficas

<div align="center">
  <img src="https://raw.githubusercontent.com/Luk343/super-cuencas/main/assets/super_cuencas_logo.png?v=2" alt="Super Cuencas Logo" width="320">
</div>

<div align="center">

![Versión](https://img.shields.io/badge/versión-1.0-blue?style=flat-square)
![Licencia](https://img.shields.io/badge/licencia-GPL--3.0-lightgrey?style=flat-square)
![QGIS](https://img.shields.io/badge/QGIS-3.44.10%20%7C%203.44.11-brightgreen?style=flat-square)
![Plataforma](https://img.shields.io/badge/plataforma-Windows%20%7C%20macOS%20%7C%20Linux-informational?style=flat-square)

</div>

---

## Descargas

<div align="center">

[![Descargar Script](https://img.shields.io/badge/⬇️%20Descargar-Script_super_cuencas-blue?style=for-the-badge)](https://github.com/Luk343/super-cuencas/raw/main/herramienta_cuencas.py)
[![Descargar Complemento](https://img.shields.io/badge/⬇️%20Descargar-Complemento_(.zip)-green?style=for-the-badge)](https://github.com/Luk343/super-cuencas/archive/refs/heads/main.zip)

</div>

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Características principales](#características-principales)
3. [Requisitos previos](#requisitos-previos)
4. [Instalación](#instalación)
5. [Guía de usuario](#guía-de-usuario)
6. [Solución de problemas](#solución-de-problemas)
7. [Notas para macOS](#notas-para-macos)
8. [Recursos y documentación](#recursos-y-documentación)
9. [Licencia](#licencia)

---

## Descripción

**Super Cuencas** es una herramienta de la Caja de Herramientas de QGIS que automatiza el análisis hidrológico mediante los siguientes procesos:

- Delimitación automática de cuencas hidrográficas a partir de un DEM (Modelo Digital de Elevación) y exutorios
- Cálculo de tres índices morfométricos por cuenca
- Generación de perfiles topográficos longitudinales en formato PNG
- Procesamiento estructurado en 9 pasos consecutivos

Desarrollado en la Escuela de Geografía de la Universidad Austral de Chile (UACh) para aplicaciones en análisis geomorfológico y planificación territorial.

### Compatibilidad y dependencias

Super Cuencas depende del complemento externo [Whitebox Workflows for QGIS](https://plugins.qgis.org/plugins/whitebox_workflows_for_qgis/) ([sitio oficial de Whitebox](https://whiteboxgeo.com/)) para ejecutar los algoritmos de hidrología — es un requisito obligatorio, no opcional, y sin él la herramienta no funciona. No se utiliza ningún otro complemento externo a QGIS.

El script en sí no incluye código específico de sistema operativo: usa la API de QGIS, GDAL y Whitebox Workflows. Por lo tanto, debería funcionar en cualquier plataforma donde QGIS **y** Whitebox Workflows estén disponibles — Windows, macOS o Linux (ver [descargas oficiales de QGIS](https://qgis.org/download/)).

Las pruebas concretas de este desarrollo se realizaron en **QGIS 3.44.10 y 3.44.11** (rama LTR).

### Índices morfométricos calculados

| Índice | Fórmula | Descripción |
|---|---|---|
| Índice de compacidad (Kc) | `Kc = 0.28 × P / √A` | Forma de la cuenca respecto a un círculo |
| Razón del relieve (Rr) | `Rr = (Hmax − Hmin) / Lcauce` | Pendiente media del cauce principal (m/km) |
| Densidad de drenaje (Dd) | `Dd = Lt / A` | Longitud total de cauces por unidad de área |

---

## Características principales

- **Procesamiento en 9 pasos**: Desde corrección de depresiones en el MDE hasta extracción de redes de drenaje e índices morfométricos avanzados
- **Interoperabilidad de motores**: Integración de API de QGIS, abstracción de datos raster/vectorial mediante GDAL y algoritmos de alto rendimiento con Whitebox Workflows
- **Gestión avanzada de datos**: Control automatizado de sistemas de coordenadas, validación topológica y optimización de memoria mediante archivos temporales
- **Visualización automática**: Generación de perfiles topográficos en PNG con resolución de 180 dpi

---

## Requisitos previos

### Software

- Sistema operativo compatible con QGIS: Windows, macOS o Linux (ver [Compatibilidad y dependencias](#compatibilidad-y-dependencias))
- QGIS 3.x — probado puntualmente en 3.44.10 y 3.44.11 — [descargar QGIS](https://qgis.org/download/) · [todas las versiones](https://qgis.org/downloads-list/)
- [Whitebox Workflows for QGIS](https://plugins.qgis.org/plugins/whitebox_workflows_for_qgis/) instalado y activado (Complementos → Administrar e instalar complementos → Whitebox Workflows). Más información en el [sitio oficial de Whitebox](https://whiteboxgeo.com/)
- Python con `matplotlib` disponible en el entorno de QGIS (necesario para generar perfiles)

### Datos geoespaciales

- Un DEM en formato raster (GeoTIFF recomendado)
  - Preferentemente con sistema de coordenadas proyectado en metros
  - Se puede utilizar CRS en grados geográficos activando la opción de reproyección
- Una capa vectorial de puntos de exutorios (mínimo 2), con un punto por cada cuenca a delimitar

---

## Instalación

### Opción A — Método rápido (recomendado)

1. Descarga `herramienta_cuencas.py` desde el botón de arriba
2. Abre la Caja de Herramientas de Procesos en QGIS
3. Haz clic en el ícono de Python en la barra superior
4. Selecciona "Agregar script a la caja de herramientas..."
5. Navega hasta el archivo descargado y selecciónalo

La herramienta aparecerá de inmediato bajo el grupo *Hidrología Avanzada* sin necesidad de reiniciar QGIS.

### Opción B — Instalación manual

1. Descarga `herramienta_cuencas.py`
2. Copia el archivo en la carpeta de scripts de QGIS según tu sistema operativo:

**Windows:**
```
%APPDATA%\QGIS\QGIS3\profiles\default\processing\scripts\
```

**macOS:**
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/
```

**Linux:**
```
~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts/
```

3. Cierra y vuelve a abrir QGIS. La herramienta aparecerá en la Caja de Herramientas bajo el grupo *Hidrología Avanzada*.

---

## Guía de usuario

### Parámetros de entrada

| Parámetro | Tipo | Descripción | Recomendación |
|---|---|---|---|
| DEM | Raster | Modelo Digital de Elevación | Cualquier CRS; preferir proyectado |
| Exutorios | Vectorial (puntos) | Puntos de salida de cada cuenca | Mínimo 2 puntos |
| Campo identificador | Campo de texto | Nombre de cada cuenca en la tabla de atributos | Vacío → `punto_0, punto_1...` |
| Umbral de acumulación | Entero | Celdas mínimas para definir un cauce | 500–2000 (cuencas pequeñas); 2000–5000 (grandes) |
| Distancia snap (m) | Decimal | Radio para mover exutorio al cauce más cercano | 50–200 m |
| Reproyección | Enum | Capas a reproyectar al CRS de trabajo | DEM y exutorios si están en grados |
| Método de snap | Enum | Corrección de posición de exutorios | Jenson Snap (recomendado) |
| Modo de salida | Enum | Capas unificadas, separadas o ambas | Solo unificado por defecto |
| Punto de detención | Enum | Hasta qué paso ejecutar | 0 = proceso completo |
| Carpeta de salida | Carpeta | Ubicación para guardar los resultados | Carpeta vacía dedicada |

### Archivos de salida

| Archivo | Formato | Descripción |
|---|---|---|
| `Cuencas_morfometria.shp` | Shapefile | Polígonos de cuencas con atributos: `cuenca_id`, `Area_km2`, `Perim_km`, `Kc`, `H_max_m`, `H_min_m`, `Lcauce_km`, `Rr`, `Lt_km`, `Dd` |
| `Longest_Flowpath_todas.shp` | Shapefile | Cauce más largo de cada cuenca (unificado) |
| `Streams_Vector.shp` | Shapefile | Red de drenaje vectorial completa |
| `Puntos_Corregidos.shp` | Shapefile | Posición original y corregida de cada exutorio |
| `Cuencas_[ID].shp` | Shapefile | Polígono individual por cuenca (modo separado) |
| `Longest_Flowpath_[ID].shp` | Shapefile | Cauce más largo individual (modo separado) |
| `Perfil_topografico_[ID].png` | PNG (180 dpi) | Perfil longitudinal con Hmax, Hmin, desnivel, pendiente y Rr |

---

## Solución de problemas

> 💡 Antes de reportar un problema, revisa si tu caso está cubierto aquí — cubre los errores más frecuentes de instalación, caché y backend de Whitebox.

### La herramienta no aparece en la Caja de Herramientas

**Si utilizaste la Opción A:**
- Verifica que seleccionaste el archivo correcto en "Agregar script a la caja de herramientas..."
- Confirma que es un archivo `.py`

**Si utilizaste la Opción B:**
- Verifica que el archivo está en la carpeta correcta para tu sistema operativo
- Cierra y vuelve a abrir QGIS — esta opción no se actualiza en tiempo real

---

### QGIS ejecuta una versión antigua del script

QGIS almacena una copia compilada en `__pycache__`. Elimínala según tu sistema operativo:

**Windows:**
```cmd
rmdir /s /q "%APPDATA%\QGIS\QGIS3\profiles\default\processing\scripts\__pycache__"
```

**Linux:**
```bash
rm -rf ~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__
```

**macOS:**
```bash
rm -rf ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__
```

Después elimina el archivo `.py` de la carpeta de scripts, vuelve a agregarlo y reinicia QGIS.

---

### Los perfiles PNG no se generan

`matplotlib` no está disponible en tu entorno de QGIS. Instálalo desde la consola de Python de QGIS (Complementos → Consola de Python):

```python
import subprocess
subprocess.run(["pip", "install", "matplotlib"])
```

Cierra y vuelve a abrir QGIS.

---

### H_max / H_min aparecen como NULL

Verifica que el DEM cubre completamente el área de las cuencas delimitadas. Si existen celdas sin datos (NoData) en zonas críticas, los valores resultarán NULL.

---

### Errores con Whitebox Workflows

#### Error: `ModuleNotFoundError: No module named 'pip'` o `No module named 'ensurepip'`

En Ubuntu/Debian/Pop!_OS, Whitebox requiere `pip` instalado a nivel de sistema:

```bash
sudo apt install python3-pip
```

Si `dpkg` está corrupto:
```bash
sudo dpkg --configure -a
sudo apt install python3-pip
```

Luego instala el backend:
```bash
pip3 install --user whitebox-workflows
```

---

#### Whitebox deja de funcionar después de actualizar

Las actualizaciones ocasionalmente dejan archivos corruptos. Limpia completamente la instalación anterior y permite que QGIS la reinstale:

**Windows (CMD, con QGIS cerrado):**

Obtén tu nombre de usuario:
```cmd
echo %USERNAME%
```

Ejecuta:
```cmd
rmdir /s /q "C:\Users\AQUI_VA_TU_USUARIO\AppData\Roaming\QGIS\QGIS3\profiles\default\python\whitebox_workflows_lib"
```

**Linux (Terminal, con QGIS cerrado):**

Obtén tu nombre de usuario:
```bash
whoami
```

Ejecuta:
```bash
rm -rf /home/AQUI_VA_TU_USUARIO/.local/share/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib
```

**macOS (Terminal, con QGIS cerrado):**
```bash
rm -rf ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib
```

Abre QGIS normalmente. El plugin detectará que falta el backend y lo reinstalará automáticamente. Esta solución resuelve aproximadamente el 95% de los problemas posteriores a actualizaciones.

---

#### Error: "Whitebox Workflows no disponible"

1. Ve a Complementos → Administrar e instalar complementos
2. Busca "Whitebox Workflows"
3. Marca la casilla para activarlo
4. Reinicia QGIS

---

## Notas para macOS

Las rutas en macOS siguen la misma lógica que en Linux, cambiando el prefijo a `~/Library/Application Support/...`. No se ha verificado paso a paso en un equipo macOS, pero deberían ser correctas dado que QGIS mantiene la misma estructura de perfiles en todas las plataformas.

### Rutas específicas en macOS

| Elemento | Ruta |
|---|---|
| Scripts de procesamiento | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/` |
| Caché de QGIS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__` |
| Backend de Whitebox | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib` |

### Requisitos adicionales

- Homebrew instalado (para gestionar dependencias si es necesario)
- Whitebox se instala igual que en Linux:

```bash
pip3 install --user whitebox-workflows
```

---

## Recursos y documentación

| Recurso | Enlace |
|---|---|
| Descargar QGIS (Windows, macOS, Linux) | [qgis.org/download](https://qgis.org/download/) |
| Listado completo de versiones de QGIS | [qgis.org/downloads-list](https://qgis.org/downloads-list/) |
| Documentación oficial de QGIS | [qgis.org/resources/hub](https://qgis.org/resources/hub/) |
| Documentación y manuales de Whitebox | [whiteboxgeo.com/learn](https://whiteboxgeo.com/learn.html) |

---

## Nota sobre nomenclatura

El nombre oficial de la herramienta es **Super Cuencas**, tal como aparece en la Caja de Herramientas de QGIS. El archivo fuente se denomina `super_cuencas_supremo.py`, pero para efectos de la entrega del Práctico 6 del curso Aplicaciones SIG se distribuye como `herramienta_cuencas.py` según lo especificado en la pauta. Es el mismo código; únicamente cambia el nombre del archivo en disco.

---

## Licencia

Este proyecto se distribuye bajo los términos de la [GNU General Public License v3.0 (GPL-3.0)](LICENSE), que garantiza la libertad de usar, estudiar, compartir y modificar el software, asegurando que cualquier trabajo derivado mantenga el código abierto.

---

Desarrollado en la Escuela de Geografía — Universidad Austral de Chile
