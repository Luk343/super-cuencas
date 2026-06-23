# 🌊 Super Cuencas

**Automatización hidrológica para QGIS** — Delimitación y análisis automático de cuencas hidrográficas

<div align="center">

![Super Cuencas Logo](./assets/super_cuencas_logo.svg "Super Cuencas - Automatización hidrológica para QGIS")

</div>

---

## Descargas

<div align="center">

[![Descargar Script](https://img.shields.io/badge/Descargar_Script-blue?style=for-the-badge)](https://github.com/Luk343/super-cuencas/raw/main/herramienta_cuencas.py)

[![Descargar Complemento Completo](https://img.shields.io/badge/Descargar_Complemento-green?style=for-the-badge)](https://github.com/Luk343/super-cuencas/archive/refs/heads/main.zip)

</div>

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Características principales](#características-principales)
3. [Requisitos previos](#requisitos-previos)
4. [Instalación](#instalación)
5. [Guía de usuario](#guía-de-usuario)
6. [Solución de problemas](#solución-de-problemas)
7. [Compatibilidad con macOS](#compatibilidad-con-macos)
8. [Licencia](#licencia)

---

## Descripción

**Super Cuencas** es una herramienta de la Caja de Herramientas de QGIS que automatiza el análisis hidrológico mediante los siguientes procesos:

- Delimitación automática de cuencas hidrográficas a partir de un DEM (Modelo Digital de Elevación) y exutorios
- Cálculo de tres índices morfométricos por cuenca
- Generación de perfiles topográficos longitudinales en formato PNG
- Procesamiento estructurado en 9 pasos consecutivos

Desarrollado en la Escuela de Geografía de la Universidad Austral de Chile (UACh) para aplicaciones en análisis geomorfológico y planificación territorial.

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

- QGIS 3.x (probado en 3.44.11)
- Whitebox Workflows for QGIS instalado y activado (Complementos → Administrar e instalar complementos → Whitebox Workflows)
- Python con `matplotlib` disponible en el entorno de QGIS (necesario para generar perfiles)

### Datos geoespaciales

- Un DEM en formato raster (GeoTIFF recomendado)
  - Preferentemente con sistemas de coordenadas proyectado en metros
  - Se puede utilizar CRS en grados geográficos activando la opción de reproyección
- Una capa vectorial de puntos de exutorios (mínimo 2), con un punto por cada cuenca a delimitar

---

## Instalación

### Opción A — Método rápido (recomendado)

1. Descarga `super_cuencas_supremo.py` desde el [repositorio](https://github.com/Luk343/super-cuencas/raw/main/herramienta_cuencas.py)
2. Abre la Caja de Herramientas de Procesos en QGIS
3. Haz clic en el ícono de Python en la barra superior
4. Selecciona "Agregar script a la caja de herramientas..."
5. Navega hasta el archivo descargado y selecciónalo

La herramienta aparecerá de inmediato bajo el grupo *Hidrología Avanzada* sin necesidad de reiniciar QGIS.

### Opción B — Instalación manual

1. Descarga `super_cuencas_supremo.py`
2. Copia el archivo en la carpeta de scripts de QGIS según tu sistema operativo

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

3. Cierra y vuelve a abrir QGIS. La herramienta aparecerá en la Caja de Herramientas.

---

## Guía de usuario

### Parámetros de entrada

| Parámetro | Tipo | Descripción | Recomendación |
|---|---|---|---|
| DEM | Raster | Modelo Digital de Elevación | Cualquier CRS; preferir proyectado |
| Exutorios | Vectorial (puntos) | Puntos de salida de cada cuenca | Mínimo 2 puntos |
| Campo identificador | Campo de texto | Nombre de cada cuenca en tabla de atributos | Vacío → `punto_0, punto_1...` |
| Umbral de acumulación | Entero | Celdas mínimas para definir un cauce | 500–2000 (cuencas pequeñas); 2000–5000 (grandes) |
| Distancia snap (m) | Decimal | Radio para mover exutorio al cauce más cercano | 50–200 m |
| Reproyección | Enum | Capas a reproyectar al CRS de trabajo | DEM y exutorios si están en grados |
| Método de snap | Enum | Corrección de posición de exutorios | Jenson Snap (recomendado) |
| Modo de salida | Enum | Capas unificadas, separadas o ambas | Solo unificado por defecto |
| Punto de detención | Enum | Hasta qué paso ejecutar | 0 = proceso completo |
| Carpeta de salida | Carpeta | Ubicación para guardar resultados | Carpeta vacía dedicada |

### Archivos de salida

| Archivo | Formato | Descripción |
|---|---|---|
| `Cuencas_morfometria.shp` | Shapefile | Polígonos de cuencas con atributos: `cuenca_id`, `Area_km2`, `Perim_km`, `Kc`, `H_max_m`, `H_min_m`, `Lcauce_km`, `Rr`, `Lt_km`, `Dd` |
| `Longest_Flowpath_todas.shp` | Shapefile | Cauce más largo de cada cuenca (unificado) |
| `Streams_Vector.shp` | Shapefile | Red de drenaje vectorial completa |
| `Puntos_Corregidos.shp` | Shapefile | Posición original y corregida de exutorios |
| `Cuencas_[ID].shp` | Shapefile | Polígono individual por cuenca (modo separado) |
| `Longest_Flowpath_[ID].shp` | Shapefile | Cauce más largo individual (modo separado) |
| `Perfil_topografico_[ID].png` | PNG (180 dpi) | Perfil longitudinal con Hmax, Hmin, desnivel, pendiente y Rr |

---

## Solución de problemas

### La herramienta no aparece en la Caja de Herramientas

**Si utilizaste la Opción A:**
- Verifica que seleccionaste el archivo correcto en "Agregar script a la caja de herramientas..."
- Confirma que es un archivo `.py`

**Si utilizaste la Opción B:**
- Verifica que el archivo está en la carpeta correcta para tu sistema operativo
- Cierra y vuelve a abrir QGIS — esta opción no se actualiza en tiempo real

---

### QGIS ejecuta una versión antigua del script

QGIS almacena una copia compilada en `__pycache__`. Elimina ambos:

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

Después de esto, elimina el archivo `.py` de la carpeta de scripts y vuelve a agregarlo. Cierra y reabre QGIS.

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

#### Error: "ModuleNotFoundError: No module named 'pip'" o "No module named 'ensurepip'"

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

Las actualizaciones ocasionalmente dejan archivos antiguos o corruptos. Limpia completamente la instalación anterior y permite que QGIS la reinstale:

**Windows (CMD, con QGIS cerrado):**

Obtén tu usuario:
```cmd
echo %USERNAME%
```

Ejecuta:
```cmd
rmdir /s /q "C:\Users\AQUI_VA_TU_USUARIO\AppData\Roaming\QGIS\QGIS3\profiles\default\python\whitebox_workflows_lib"
```

**Linux (Terminal, con QGIS cerrado):**

Obtén tu usuario:
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

Activa el complemento manualmente:

1. Ve a Complementos → Administrar e instalar complementos
2. Busca "Whitebox Workflows"
3. Marca la casilla para activarlo
4. Reinicia QGIS

---

## Compatibilidad con macOS

Super Cuencas es compatible con macOS 10.15 y versiones posteriores, con QGIS 3.x instalado.

### Rutas específicas en macOS

| Elemento | Ruta |
|---|---|
| Scripts de procesamiento | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/` |
| Caché de QGIS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts/__pycache__` |
| Backend de Whitebox | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/whitebox_workflows_lib` |

### Requisitos adicionales

- Homebrew instalado (para gestionar dependencias si es necesario)
- Whitebox se instala de la siguiente manera:

```bash
pip3 install --user whitebox-workflows
```

Los problemas comunes (Whitebox no disponible, perfiles PNG no generan) tienen las mismas soluciones que en Windows y Linux, únicamente varían las rutas de carpetas.

---

## Nota sobre nomenclatura

El nombre oficial de la herramienta es **Super Cuencas**, tal como aparece en la Caja de Herramientas de QGIS. El archivo fuente del proyecto se denomina `super_cuencas_supremo.py`, pero para efectos de la entrega del Práctico 6 del curso Aplicaciones SIG, se distribuye como `herramienta_cuencas.py` según lo especificado en la pauta del curso.

Es el mismo código; únicamente cambia el nombre del archivo en disco.

---

## Licencia

Este proyecto se distribuye bajo los términos de la [GNU General Public License v3.0 (GPL-3.0)](LICENSE).

Garantiza las siguientes libertades:

- Usar el software
- Estudiar el código
- Compartir el software
- Modificar el software

Con la garantía de que cualquier trabajo derivado mantendrá el código abierto.

---

## Enlaces útiles

- [Repositorio GitHub](https://github.com/Luk343/super-cuencas)
- [Descargar script](https://github.com/Luk343/super-cuencas/raw/main/herramienta_cuencas.py)
- [Descargar complemento completo (.zip)](https://github.com/Luk343/super-cuencas/archive/refs/heads/main.zip)

---

Desarrollado en la Escuela de Geografía — Universidad Austral de Chile

---

**Nota sobre el logo:** El archivo `super_cuencas_logo.svg` debe estar ubicado en la carpeta `assets/` en la raíz del repositorio. Si descargas este README, asegúrate de mantener esta estructura de directorios para que la imagen se muestre correctamente:

```
tu-repositorio/
├── README.md
├── assets/
│   └── super_cuencas_logo.svg
└── herramienta_cuencas.py
```
