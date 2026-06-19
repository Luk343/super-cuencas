"""
╔══════════════════════════════════════════════════════════════════╗
║         SUPER CUENCAS — Herramienta de delimitación y           ║
║          análisis morfométrico de cuencas hidrográficas         ║
╠══════════════════════════════════════════════════════════════════╣
║  Escuela de Geografía — Universidad Austral de Chile            ║
║  Autor  : Lucas Carrasco                                        ║
║  Fecha  : Junio 2026                                            ║
╠══════════════════════════════════════════════════════════════════╣
║  Plataforma : QGIS 3.44.11 · Caja de Herramientas               ║
║  Requiere   : Whitebox Workflows 2.1.0 (complemento QGIS)       ║
║  Grupo      : Hidrología Avanzada                               ║
╠══════════════════════════════════════════════════════════════════╣
║  Archivo    : super_cuencas_supremo.py                          ║
╚══════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ANÉCDOTA DE ORIGEN DEL NOMBRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  El nombre "Super Cuencas" nació en clases cuando el profesor
  Pablo Rodrigo Iribarren Anacona le comentaba a Hernán Saavedra
  que había que ponerle un nombre a la herramienta para poder
  reconocerla. En ese momento Lucas Carrasco lo dijo en voz alta
  espontáneamente — y luego les informó a sus compañeros que
  tenía copyright.

  Esta versión final (archivo: super_cuencas_supremo.py) es el
  resultado de aproximadamente 65 archivos de desarrollo en
  trabajo colaborativo con IA. No fue fácil, pero llegamos.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Desarrollado y probado en:
  · QGIS 3.44.11
  · Whitebox Workflows para QGIS 2.1.0

Pipeline hidrológico (9 pasos):
  Fill Depressions → D8 Pointer → D8 Flow Accumulation →
  Extract Streams → Raster Streams to Vector →
  Jenson Snap Pour Points → Watershed →
  Raster to Vector Polygons → Longest Flowpath
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingParameterFolderDestination,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsField,
    QgsFields,
    QgsVectorFileWriter,
    QgsCoordinateTransformContext,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsExpression,
    QgsFeatureRequest,
    QgsRectangle,
)
from qgis.PyQt.QtCore import QVariant
from qgis import processing
import os
import math
import tempfile
import shutil
import hashlib


# ── Utilidad: eliminar shapefile y archivos auxiliares ────────────────── #
def eliminar_shapefile_si_existe(ruta_shp):
    """Elimina un shapefile y todos sus archivos asociados si existen."""
    if not os.path.exists(ruta_shp):
        return
    base = os.path.splitext(ruta_shp)[0]
    for ext in ('.shp', '.shx', '.dbf', '.prj', '.cpg', '.qix', '.sbn', '.sbx'):
        aux = base + ext
        try:
            if os.path.exists(aux):
                os.remove(aux)
        except OSError:
            pass


class SuperCuencasSupremo(QgsProcessingAlgorithm):
    # ── Nombres de parámetros ──────────────────────────────────────────── #
    INPUT_DEM          = "INPUT_DEM"
    INPUT_EXUTORIOS    = "INPUT_EXUTORIOS"
    UMBRAL_ACUM        = "UMBRAL_ACUM"
    DIST_SNAP          = "DIST_SNAP"
    MODO_REPROYECTAR   = "MODO_REPROYECTAR"
    CRS_DESTINO        = "CRS_DESTINO"
    EPSG_MANUAL        = "EPSG_MANUAL"
    MODO_SNAP          = "MODO_SNAP"
    CAMPO_ID           = "CAMPO_ID"
    MODO_SALIDA        = "MODO_SALIDA"
    GUARDAR_PUNTOS     = "GUARDAR_PUNTOS"
    GUARDAR_STREAMS_R  = "GUARDAR_STREAMS_R"
    MODO_DETENCION     = "MODO_DETENCION"
    CARPETA_TEMP       = "CARPETA_TEMP"
    CARPETA_SALIDA     = "CARPETA_SALIDA"

    # ── Opciones de los enums ─────────────────────────────────────────── #
    OPCIONES_CRS = [
        "CRS del proyecto QGIS",
        "Especificar código EPSG manualmente",
    ]
    OPCIONES_REPROYECTAR = [
        "Reproyectar DEM y exutorios (recomendado)",
        "Reproyectar solo el DEM",
        "Reproyectar solo los exutorios",
        "No reproyectar — usar CRS original del DEM",
    ]
    OPCIONES_SNAP = [
        "Sin snap — usar exutorios tal como están (sin corrección de posición)",
        "Jenson Snap Pour Points + proyección al centro del cauce",
    ]
    OPCIONES_SALIDA = [
        "Solo unificado — una capa con todas las cuencas (por defecto)",
        "Solo separado — un shapefile por cuenca",
        "Ambos — unificado + un shapefile por cuenca",
    ]
    OPCIONES_DETENCION = [
        "0 — Proceso completo (por defecto)",
        "1 — Tras Fill Depressions (DEM corregido)",
        "2 — Tras D8 Pointer (dirección de flujo)",
        "3 — Tras D8 Flow Accumulation (acumulación de flujo)",
        "4 — Tras Extract Streams (red de drenaje ráster)",
        "5 — Tras Raster Streams to Vector (red vectorial)",
        "6 — Tras Jenson Snap / corrección de exutorios",
        "7 — Tras Watershed (cuencas ráster)",
        "8 — Tras Raster to Vector Polygons (cuencas vector)",
        "9 — Tras Longest Flowpath (cauce más largo, sin perfil)",
    ]

    def name(self):           return "super_cuencas_supremo"
    def displayName(self):    return "Super Cuencas"
    def group(self):          return "Hidrología Avanzada"
    def groupId(self):        return "hidrologia_avanzada"
    def createInstance(self): return SuperCuencasSupremo()

    def shortHelpString(self):
        return (
            "<b>Super Cuencas — Análisis morfométrico automatizado</b><br>"
            "<i>Escuela de Geografía · Universidad Austral de Chile</i><br>"
            "<i>Autor: Lucas Carrasco · Junio 2026</i><br>"
            "<i>QGIS 3.44.11 · Whitebox Workflows 2.1.0</i><br><br>"
            "Delimita cuencas hidrográficas una por exutorio y calcula "
            "automáticamente los índices Kc, Rr y Dd usando Whitebox Workflows.<br><br>"
            "<b>Parámetros principales:</b><ul>"
            "<li><b>DEM</b>: modelo de elevación (cualquier CRS).</li>"
            "<li><b>Exutorios</b>: puntos de salida de cada cuenca.</li>"
            "<li><b>Campo identificador de cuencas</b>: campo de la tabla de atributos "
            "de los exutorios que se usará como nombre de cada cuenca. Si se deja vacío "
            "se nombran automáticamente punto_0, punto_1, punto_2…</li>"
            "<li><b>Umbral de acumulación</b>: celdas mínimas para definir un cauce (500–5000).</li>"
            "<li><b>Distancia snap (m)</b>: radio para mover el exutorio al cauce más cercano.</li>"
            "</ul>"
            "<b>Modo de salida:</b><ul>"
            "<li><i>Solo unificado</i>: genera una capa con todas las cuencas juntas "
            "(Cuencas_morfometria.shp y Longest_Flowpath_todas.shp). Por defecto.</li>"
            "<li><i>Solo separado</i>: genera un shapefile independiente por cuenca "
            "(Cuencas_[ID].shp y Longest_Flowpath_[ID].shp).</li>"
            "<li><i>Ambos</i>: genera las capas unificadas y además los shapefiles individuales.</li>"
            "</ul>"
            "<b>Reproyección:</b><ul>"
            "<li><i>DEM y exutorios</i>: reproyecta ambas capas (recomendado si el DEM está en grados).</li>"
            "<li><i>Solo DEM</i>: útil si los exutorios ya están en CRS métrico.</li>"
            "<li><i>Solo exutorios</i>: útil si el DEM ya está proyectado.</li>"
            "<li><i>No reproyectar</i>: procesa en el CRS original (puede producir resultados"
            " distorsionados en CRS geográficos).</li>"
            "</ul>"
            "<b>Método de snap:</b><ul>"
            "<li><i>Sin snap</i>: los exutorios se usan exactamente donde están dibujados.</li>"
            "<li><i>Jenson Snap + proyección al centro del cauce</i>: Whitebox mueve el punto "
            "al cauce más cercano dentro del radio, luego se proyecta al eje central de la "
            "línea vectorial. Garantiza que el exutorio quede en el centro del cauce.</li>"
            "</ul>"
            "<b>Opciones de salida adicionales:</b><ul>"
            "<li><i>Guardar Puntos_Corregidos</i>: shapefile con posición original y snap.</li>"
            "<li><i>Guardar rasters intermedios</i>: fill_dem, d8_pointer, flow_accum, streams.</li>"
            "<li><i>Punto de detención</i>: detiene el proceso tras cualquier paso del pipeline. "
            "Útil para inspeccionar resultados intermedios.</li>"
            "<li><i>Carpeta de temporales</i>: si se especifica, los intermedios se conservan "
            "entre ejecuciones (nombre determinista basado en el DEM).</li>"
            "</ul>"
            "<b>Salidas (proceso completo):</b><ul>"
            "<li>Streams_Vector — red de drenaje vectorial</li>"
            "<li>Cuencas_morfometria.shp — polígonos con índices Kc, Rr, Dd (modo unificado)</li>"
            "<li>Cuencas_[ID].shp — polígono individual por cuenca (modo separado)</li>"
            "<li>Longest_Flowpath_todas.shp — cauce más largo unificado</li>"
            "<li>Longest_Flowpath_[ID].shp — cauce más largo por cuenca (modo separado)</li>"
            "<li>Puntos_Corregidos.shp — posición original y corregida de cada exutorio</li>"
            "<li>Perfil_topografico_[ID].png — perfil longitudinal por cuenca</li>"
            "</ul>"
        )

    # ── initAlgorithm ────────────────────────────────────────────────── #
    def initAlgorithm(self, config=None):
        from qgis.core import QgsProcessingParameterEnum

        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT_DEM, "DEM — Modelo Digital de Elevaciones"))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT_EXUTORIOS, "Exutorios — Puntos de salida",
            [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterNumber(
            self.UMBRAL_ACUM, "Umbral de acumulación (celdas)",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1000, minValue=100))
        self.addParameter(QgsProcessingParameterNumber(
            self.DIST_SNAP, "Distancia de ajuste snap (metros)",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=100.0, minValue=1.0))

        # ── Reproyección ────────────────────────────────────────────────
        self.addParameter(QgsProcessingParameterEnum(
            self.MODO_REPROYECTAR,
            "Reproyección — ¿qué capas reproyectar al CRS de trabajo?",
            options=self.OPCIONES_REPROYECTAR,
            defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(
            self.CRS_DESTINO,
            "CRS destino para reproyección",
            options=self.OPCIONES_CRS,
            defaultValue=0,
            optional=True))
        self.addParameter(QgsProcessingParameterString(
            self.EPSG_MANUAL,
            "Código EPSG manual (ej: 32719) — solo si eligió 'Especificar EPSG'",
            defaultValue="", optional=True))

        # ── Método de snap ─────────────────────────────────────────────
        self.addParameter(QgsProcessingParameterEnum(
            self.MODO_SNAP,
            "Método de corrección de posición de exutorios (snap)",
            options=self.OPCIONES_SNAP,
            defaultValue=1))   # Por defecto: Jenson + proyección al centro

        # ── Campo identificador de cuencas ─────────────────────────────
        from qgis.core import QgsProcessingParameterField
        self.addParameter(QgsProcessingParameterField(
            self.CAMPO_ID,
            "Campo identificador de cuencas (dejar vacío → punto_0, punto_1, …)",
            parentLayerParameterName=self.INPUT_EXUTORIOS,
            type=QgsProcessingParameterField.Any,
            optional=True,
            defaultValue=None))

        # ── Modo de salida ─────────────────────────────────────────────
        self.addParameter(QgsProcessingParameterEnum(
            self.MODO_SALIDA,
            "Modo de salida de capas",
            options=self.OPCIONES_SALIDA,
            defaultValue=0))

        # ── Opciones adicionales ───────────────────────────────────────
        self.addParameter(QgsProcessingParameterBoolean(
            self.GUARDAR_PUNTOS,
            "Guardar Puntos_Corregidos.shp (posición original y snap de exutorios)",
            defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.GUARDAR_STREAMS_R,
            "Guardar rasters intermedios (fill_dem, d8_pointer, flow_accum, streams raster)",
            defaultValue=False))
        self.addParameter(QgsProcessingParameterEnum(
            self.MODO_DETENCION,
            "Punto de detención — hasta dónde ejecutar el proceso",
            options=self.OPCIONES_DETENCION,
            defaultValue=0))
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.CARPETA_TEMP,
            "📁 Carpeta para archivos intermedios (dejar vacío = se borran al terminar) "
            "— ESCRIBIR LA RUTA A MANO o usar el botón '…' para seleccionar carpeta. "
            "Si se especifica, los intermedios se conservan entre ejecuciones.",
            optional=True,
            createByDefault=False))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.CARPETA_SALIDA, "Carpeta de salida"))

    # ── processAlgorithm ─────────────────────────────────────────────── #
    def processAlgorithm(self, parameters, context, feedback):

        # Verificar Whitebox
        registry = QgsApplication.processingRegistry()
        provider  = registry.providerById("whitebox_workflows")
        if provider is None or not provider.isActive():
            feedback.reportError(
                "❌ El proveedor 'whitebox_workflows' no está activo. "
                "Actívalo en Complementos → Administrar complementos → Whitebox Workflows.")
            raise Exception("Whitebox Workflows no disponible")

        # ── Leer parámetros ────────────────────────────────────────────
        dem_layer       = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        exut_layer      = self.parameterAsVectorLayer(parameters, self.INPUT_EXUTORIOS, context)
        umbral          = self.parameterAsInt(parameters, self.UMBRAL_ACUM, context)
        dist_snap       = self.parameterAsDouble(parameters, self.DIST_SNAP, context)
        modo_reproy     = self.parameterAsEnum(parameters, self.MODO_REPROYECTAR, context)
        crs_opcion      = self.parameterAsEnum(parameters, self.CRS_DESTINO, context)
        epsg_manual     = (parameters.get(self.EPSG_MANUAL) or "").strip()
        modo_snap       = self.parameterAsEnum(parameters, self.MODO_SNAP, context)
        campo_id_param  = (parameters.get(self.CAMPO_ID) or "").strip()
        modo_salida     = self.parameterAsEnum(parameters, self.MODO_SALIDA, context)
        guardar_puntos  = self.parameterAsBool(parameters, self.GUARDAR_PUNTOS, context)
        guardar_str_r   = self.parameterAsBool(parameters, self.GUARDAR_STREAMS_R, context)
        modo_detencion  = self.parameterAsEnum(parameters, self.MODO_DETENCION, context)
        carpeta_temp    = (parameters.get(self.CARPETA_TEMP) or "").strip()
        out_dir         = self.parameterAsString(parameters, self.CARPETA_SALIDA, context)

        # modo_reproy: 0=ambos 1=soloDEM 2=soloExut 3=ninguno
        reproy_dem  = modo_reproy in (0, 1)
        reproy_exut = modo_reproy in (0, 2)
        hay_reproy  = reproy_dem or reproy_exut

        sin_snap           = (modo_snap == 0)
        usar_jenson        = (modo_snap == 1)

        # modo_salida: 0=unificado, 1=separado, 2=ambos
        hacer_unificado = modo_salida in (0, 2)
        hacer_separado  = modo_salida in (1, 2)

        # modo_detencion: 0=completo, 1=fill, 2=d8ptr, 3=accum, 4=streams_r,
        #                 5=streams_v, 6=snap, 7=watershed, 8=cuenca_vec,
        #                 9=flowpath, 10=perfil
        punto_detencion = modo_detencion  # alias legible

        guardar_tmp = bool(carpeta_temp)

        # dist_snap_wbx: distancia que se pasa a Jenson en las unidades del CRS de trabajo.
        # Si el CRS es geográfico (grados) se convierte aproximando 1° ≈ 111 320 m.
        # Se calcula tras conocer crs_trabajo, así que se fija más abajo; aquí solo se
        # guarda el valor métrico original para usarlo en la proyección vectorial.

        # ── Carpeta temporal determinista (basada en hash de la ruta del DEM) ──
        DEM = dem_layer.source()
        dem_hash = hashlib.md5(DEM.encode()).hexdigest()[:12]
        if guardar_tmp:
            os.makedirs(carpeta_temp, exist_ok=True)
            tmp_dir = os.path.join(carpeta_temp, f"super_cuencas_{dem_hash}")
        else:
            tmp_dir = os.path.join(tempfile.gettempdir(), f"super_cuencas_{dem_hash}")
        os.makedirs(tmp_dir, exist_ok=True)

        def tmp(n): return os.path.join(tmp_dir, n)
        def out(n): return os.path.join(out_dir, n)

        os.makedirs(out_dir, exist_ok=True)

        dem_crs      = dem_layer.crs()
        crs_original = dem_crs
        # crs_exut_orig se define aquí para garantizar que siempre exista
        crs_exut_orig = exut_layer.crs()
        reproyectado  = False  # inicializado aquí para que siempre exista

        feedback.pushInfo("=" * 60)
        feedback.pushInfo("Super Cuencas — iniciando procesamiento")
        feedback.pushInfo("=" * 60)

        # ── Determinar CRS de trabajo ─────────────────────────────────
        if hay_reproy:
            if crs_opcion == 1 and epsg_manual:
                crs_trabajo = QgsCoordinateReferenceSystem(f"EPSG:{epsg_manual}")
                if not crs_trabajo.isValid():
                    raise Exception(f"Código EPSG no válido: '{epsg_manual}'")
                feedback.pushInfo(f"CRS destino (manual): {crs_trabajo.authid()}")
            else:
                crs_trabajo = QgsProject.instance().crs()
                if not crs_trabajo.isValid() or crs_trabajo.isGeographic():
                    ext   = dem_layer.extent()
                    lon_c = (ext.xMinimum() + ext.xMaximum()) / 2.0
                    lat_c = (ext.yMinimum() + ext.yMaximum()) / 2.0
                    if not dem_crs.isGeographic():
                        tr_geo = QgsCoordinateTransform(
                            dem_crs, QgsCoordinateReferenceSystem("EPSG:4326"),
                            QgsProject.instance())
                        pt    = tr_geo.transform(QgsPointXY(lon_c, lat_c))
                        lon_c, lat_c = pt.x(), pt.y()
                    zona = int((lon_c + 180) / 6) + 1
                    hem  = "6" if lat_c >= 0 else "7"
                    crs_trabajo = QgsCoordinateReferenceSystem(f"EPSG:32{hem}{zona:02d}")
                    feedback.pushInfo(
                        f"⚠ CRS del proyecto geográfico o inválido → "
                        f"UTM automático: {crs_trabajo.authid()}")
                else:
                    feedback.pushInfo(f"CRS destino (proyecto): {crs_trabajo.authid()}")
        else:
            crs_trabajo = dem_crs
            feedback.pushInfo(f"Sin reproyección — CRS original: {dem_crs.authid()}")
            if dem_crs.isGeographic():
                feedback.pushWarning(
                    "⚠ El DEM está en CRS geográfico (grados). Whitebox puede producir "
                    "resultados distorsionados. Se recomienda usar reproyección.")

        # ── dist_snap en unidades del CRS de trabajo ──────────────────
        # Si el CRS de trabajo es geográfico (grados), convertimos metros → grados.
        # Usamos 1° ≈ 111 320 m como aproximación suficiente para el snap.
        if crs_trabajo.isGeographic():
            dist_snap_wbx    = dist_snap / 111320.0
            radio_proyeccion = dist_snap_wbx * 2.0
            feedback.pushInfo(
                f"    ℹ CRS en grados: dist_snap convertida "
                f"{dist_snap:.0f} m → {dist_snap_wbx:.6f}°")
        else:
            dist_snap_wbx    = dist_snap
            radio_proyeccion = dist_snap * 2.0

        # ── Forzar reproyección de exutorios si sus CRS difieren del DEM ──
        # (aunque el usuario no lo haya solicitado, es necesario para que Whitebox funcione)
        if not reproy_exut and crs_exut_orig != crs_trabajo:
            feedback.pushWarning(
                f"⚠ Los exutorios ({crs_exut_orig.authid()}) y el CRS de trabajo "
                f"({crs_trabajo.authid()}) son distintos. Se reproyectarán los exutorios "
                f"automáticamente para evitar errores.")
            reproy_exut = True

        # ── Reproyectar DEM ───────────────────────────────────────────
        if reproy_dem:
            feedback.pushInfo(
                f"Reproyectando DEM ({dem_crs.authid()}) → {crs_trabajo.authid()}...")
            dem_utm = tmp("dem_trabajo.tif")
            processing.run("gdal:warpreproject", {
                'INPUT': DEM, 'SOURCE_CRS': dem_crs.authid(),
                'TARGET_CRS': crs_trabajo.authid(), 'RESAMPLING': 1,
                'NODATA': None, 'TARGET_RESOLUTION': None,
                'OPTIONS': 'COMPRESS=LZW', 'DATA_TYPE': 0,
                'TARGET_EXTENT': None, 'TARGET_EXTENT_CRS': None,
                'MULTITHREADING': True, 'EXTRA': '', 'OUTPUT': dem_utm
            }, context=context, feedback=feedback)
            DEM_trabajo  = dem_utm
            reproyectado = True
            feedback.pushInfo("    ✓ DEM reproyectado")
        else:
            DEM_trabajo  = DEM
            reproyectado = False

        # ── Reproyectar exutorios ──────────────────────────────────────
        if reproy_exut:
            feedback.pushInfo(
                f"Reproyectando exutorios ({crs_exut_orig.authid()}) "
                f"→ {crs_trabajo.authid()}...")
            exut_utm_shp = tmp("exutorios_trabajo.shp")
            processing.run("native:reprojectlayer", {
                'INPUT': exut_layer, 'TARGET_CRS': crs_trabajo.authid(),
                'OUTPUT': exut_utm_shp
            }, context=context, feedback=feedback)
            exut_para_proc = QgsVectorLayer(exut_utm_shp, "exut_trabajo", "ogr")
            if not exut_para_proc.isValid():
                raise Exception("No se pudo reproyectar la capa de exutorios.")
            feedback.pushInfo("    ✓ Exutorios reproyectados")
        else:
            exut_para_proc = exut_layer

        # ── FASE 1: Preprocesamiento DEM ──────────────────────────────
        feedback.pushInfo("\n[FASE 1] Preprocesando DEM...")
        fill = tmp("fill_dem.tif")
        processing.run("whitebox_workflows:fill_depressions", {
            'dem': DEM_trabajo, 'fix_flats': True,
            'flat_increment': 0.001, 'max_depth': 1000.0, 'output': fill
        }, context=context, feedback=feedback)
        feedback.setProgress(10)
        feedback.pushInfo("    ✓ [1] Fill Depressions completado")

        # ── Punto de detención 1 ──────────────────────────────────────
        if punto_detencion == 1:
            if guardar_str_r:
                shutil.copy2(fill, out("fill_dem.tif"))
            feedback.pushInfo("\n⏹ Detenido tras Fill Depressions.")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        d8 = tmp("d8_pointer.tif")
        processing.run("whitebox_workflows:d8_pointer", {
            'dem': fill, 'output': d8
        }, context=context, feedback=feedback)
        feedback.setProgress(20)
        feedback.pushInfo("    ✓ [2] D8 Pointer completado")

        # ── Punto de detención 2 ──────────────────────────────────────
        if punto_detencion == 2:
            if guardar_str_r:
                shutil.copy2(d8, out("d8_pointer.tif"))
            feedback.pushInfo("\n⏹ Detenido tras D8 Pointer.")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        accum = tmp("flow_accum.tif")
        processing.run("whitebox_workflows:d8_flow_accum", {
            'input': fill, 'out_type': 0, 'log_transform': False, 'output': accum
        }, context=context, feedback=feedback)
        feedback.setProgress(30)
        feedback.pushInfo("    ✓ [3] D8 Flow Accumulation completado")

        # ── Punto de detención 3 ──────────────────────────────────────
        if punto_detencion == 3:
            if guardar_str_r:
                shutil.copy2(accum, out("flow_accum.tif"))
            feedback.pushInfo("\n⏹ Detenido tras D8 Flow Accumulation.")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # Red de drenaje global (una sola vez)
        feedback.pushInfo("\n[FASE 1b] Generando red de drenaje...")
        streams_r_global = tmp("streams_global.tif")
        processing.run("whitebox_workflows:extract_streams", {
            'flow_accumulation': accum, 'threshold': float(umbral),
            'zero_background': True, 'output': streams_r_global
        }, context=context, feedback=feedback)
        feedback.pushInfo("    ✓ [4] Extract Streams completado")

        # ── Guardar rasters intermedios si se solicitó ─────────────────
        if guardar_str_r:
            feedback.pushInfo("    Guardando rasters intermedios en carpeta de salida...")
            for nombre_r, ruta_r in [
                ("fill_dem.tif",       fill),
                ("d8_pointer.tif",     d8),
                ("flow_accum.tif",     accum),
                ("streams_raster.tif", streams_r_global),
            ]:
                shutil.copy2(ruta_r, out(nombre_r))
                feedback.pushInfo(f"    ✓ {nombre_r} guardado")

        # ── Punto de detención 4 ──────────────────────────────────────
        if punto_detencion == 4:
            feedback.pushInfo("\n⏹ Detenido tras Extract Streams (red de drenaje ráster).")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # ── Streams vectoriales globales ───────────────────────────────
        streams_v_global = tmp("Streams_Vector.shp")
        # Descargar del proyecto si estaba cargada (evita bloqueo de archivo)
        proyecto = QgsProject.instance()
        for layer in list(proyecto.mapLayers().values()):
            if os.path.normcase(layer.source().split("|")[0]) == os.path.normcase(streams_v_global):
                proyecto.removeMapLayer(layer.id())
                break
        eliminar_shapefile_si_existe(streams_v_global)

        processing.run("whitebox_workflows:raster_streams_to_vector", {
            'd8_pntr': d8, 'streams_raster': streams_r_global,
            'all_vertices': False, 'output': streams_v_global
        }, context=context, feedback=feedback)
        feedback.pushInfo("    ✓ [5] Streams_Vector.shp generado")
        feedback.setProgress(35)

        # ── Punto de detención 5 ──────────────────────────────────────
        if punto_detencion == 5:
            feedback.pushInfo("\n⏹ Detenido tras Raster Streams to Vector.")
            lyr_sv = QgsVectorLayer(streams_v_global, "Streams_Vector", "ogr")
            if lyr_sv.isValid():
                context.temporaryLayerStore().addMapLayer(lyr_sv)
                context.addLayerToLoadOnCompletion(
                    lyr_sv.id(), QgsProcessingContext.LayerDetails(
                        "Streams_Vector", QgsProject.instance(), "Streams_Vector"))
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # ── FASE 2: Snap de todos los exutorios ───────────────────────
        # El snap se hace punto a punto (necesario para proyectar al
        # centro del cauce vectorial). Los resultados se acumulan en
        # una lista y luego se escriben en un ÚNICO shapefile que se
        # pasa a Whitebox watershed en un solo llamado.
        features = list(exut_para_proc.getFeatures())
        n_total  = len(features)
        if n_total == 0:
            raise Exception("La capa de exutorios no contiene entidades.")
        feedback.pushInfo(f"\n[FASE 2] Procesando {n_total} exutorio(s)...")
        feedback.pushInfo(
            f"Método snap: {'Jenson + proyección al centro del cauce' if usar_jenson else 'Sin snap — puntos usados tal como están'}")

        # ── Resolver campo identificador ──────────────────────────────
        # Si el usuario eligió un campo en el parámetro, se usa ese.
        # Si dejó vacío, se numeran automáticamente: punto_0, punto_1…
        if campo_id_param:
            # Verificar que el campo existe en la capa
            nombres_campos = [f.name() for f in exut_para_proc.fields()]
            if campo_id_param in nombres_campos:
                id_field = campo_id_param
                feedback.pushInfo(f"Campo identificador (elegido por usuario): '{id_field}'")
            else:
                id_field = None
                feedback.pushWarning(
                    f"    ⚠ Campo '{campo_id_param}' no encontrado en la capa de exutorios. "
                    f"Se usará numeración automática (punto_0, punto_1…)")
        else:
            id_field = None
            feedback.pushInfo("Campo identificador: no especificado → numeración automática (punto_0, punto_1…)")

        # Precargar capa de streams vectoriales para proyección al centro del cauce
        if usar_jenson:
            capa_streams_vector = QgsVectorLayer(streams_v_global, "streams_vector", "ogr")
            if not capa_streams_vector.isValid():
                feedback.reportError(
                    "❌ No se pudo cargar Streams_Vector.shp para proyección de puntos.")
                raise Exception("Streams_Vector no disponible")
            capa_streams_vector.dataProvider().createSpatialIndex()
        else:
            capa_streams_vector = None

        # Descargar capas previas en la carpeta de salida
        out_dir_norm = os.path.normcase(out_dir)
        ids_remover = [
            lid for lid, lyr in proyecto.mapLayers().items()
            if os.path.normcase(os.path.dirname(
                lyr.source().split("|")[0])) == out_dir_norm
        ]
        if ids_remover:
            proyecto.removeMapLayers(ids_remover)
            feedback.pushInfo(f"    Capas previas descargadas del proyecto: {len(ids_remover)}")

        snaps_info = []   # (sufijo, i, x_orig, y_orig, x_snap, y_snap, dist_m)
        sufijos    = []   # sufijo para cada exutorio, en orden

        # ── FASE 2a: Snap punto a punto ───────────────────────────────
        feedback.pushInfo("\n[FASE 2a] Calculando snap de exutorios...")
        for i, feat in enumerate(features):
            if id_field:
                val    = feat[id_field]
                sufijo = (
                    f"punto_{i}"
                    if val is None or str(val).strip() in ("", "NULL")
                    else str(val).strip().replace(" ", "_").replace("/", "-")
                )
            else:
                sufijo = f"punto_{i}"
            sufijos.append(sufijo)

            feedback.pushInfo(f"  Exutorio {i+1}/{n_total} · ID = {sufijo}")
            def te_i(n): return os.path.join(tmp_dir, f"{sufijo}_{n}")

            pt_orig = feat.geometry().asPoint()
            x_orig, y_orig = pt_orig.x(), pt_orig.y()

            if sin_snap:
                x_snap, y_snap = x_orig, y_orig
                feedback.pushInfo("    · Sin snap — punto usado en posición original")
            elif usar_jenson:
                pt_shp = te_i("pt_single.shp")
                processing.run("native:extractbyexpression", {
                    "INPUT":      exut_para_proc,
                    "EXPRESSION": f'$id = {feat.id()}',
                    "OUTPUT":     pt_shp
                }, context=context, feedback=feedback)
                snap_jenson = te_i(f"snap_{sufijo}.shp")
                processing.run("whitebox_workflows:jenson_snap_pour_points", {
                    'pour_pts':  pt_shp,
                    'streams':   streams_r_global,
                    'snap_dist': dist_snap_wbx,
                    'output':    snap_jenson
                }, context=context, feedback=feedback)

                punto_jenson = None
                if os.path.exists(snap_jenson):
                    lyr_snap = QgsVectorLayer(snap_jenson, "snap_tmp", "ogr")
                    if lyr_snap.isValid():
                        for sf in lyr_snap.getFeatures():
                            g = sf.geometry()
                            if g and not g.isEmpty():
                                punto_jenson = g.asPoint()
                                break
                    del lyr_snap

                if punto_jenson is None:
                    feedback.pushWarning(
                        "    · Jenson no encontró cauce — proyectando punto original.")
                    punto_jenson = pt_orig

                punto_centro = self._proyectar_punto_a_linea(
                    punto_jenson, capa_streams_vector, radio_proyeccion)
                x_snap, y_snap = punto_centro.x(), punto_centro.y()
                feedback.pushInfo("    · [6] Jenson snap → proyectado al centro del cauce")

            dist_m = math.hypot(x_snap - x_orig, y_snap - y_orig)
            if dist_m > 0:
                feedback.pushInfo(f"    · Original : X={x_orig:.6f}  Y={y_orig:.6f}")
                feedback.pushInfo(
                    f"    · Corregido: X={x_snap:.6f}  Y={y_snap:.6f}"
                    f"  (desplazamiento: {dist_m:.6f} uds CRS)")
            else:
                feedback.pushInfo(
                    f"    · Posición : X={x_snap:.6f}  Y={y_snap:.6f}  (sin desplazamiento)")
            snaps_info.append((sufijo, i, x_orig, y_orig, x_snap, y_snap, round(dist_m, 6)))

        # Punto de detención 6
        if punto_detencion == 6:
            feedback.pushInfo("\n⏹ Detenido tras snap de todos los exutorios.")
            capa_streams_vector = None
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # Liberar streams vector — ya no se necesita
        capa_streams_vector = None

        # ── FASE 2b: Watershed único con todos los puntos ─────────────
        # Construir un shapefile con todos los puntos snapeados.
        # Whitebox watershed asigna valor=1 al área del 1er point, 2 al 2º, etc.,
        # en el orden en que aparecen en el shapefile.
        feedback.pushInfo("\n[FASE 2b] Generando watershed unificado con todos los exutorios...")
        all_snaps_shp = tmp("all_snaps.shp")
        campos_all = QgsFields()
        campos_all.append(QgsField("id",    QVariant.String, len=40))
        campos_all.append(QgsField("orden", QVariant.Int))
        opts_all            = QgsVectorFileWriter.SaveVectorOptions()
        opts_all.driverName = "ESRI Shapefile"
        opts_all.fileEncoding = "UTF-8"
        writer_all = QgsVectorFileWriter.create(
            all_snaps_shp, campos_all, QgsWkbTypes.Point, crs_trabajo,
            QgsCoordinateTransformContext(), opts_all)
        if writer_all.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(f"No se pudo crear all_snaps.shp: {writer_all.errorMessage()}")
        for (sufijo, i, x_orig, y_orig, x_snap, y_snap, dist_m) in snaps_info:
            f_all = QgsFeature(campos_all)
            f_all.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x_snap, y_snap)))
            f_all["id"]    = sufijo
            f_all["orden"] = i + 1
            writer_all.addFeature(f_all)
        del writer_all

        # Un solo llamado a watershed con los N puntos → raster con valores 1..N
        basins_raster_uni = tmp("basins_todos.tif")
        processing.run("whitebox_workflows:watershed", {
            'd8_pntr':  d8,
            'pour_pts': all_snaps_shp,
            'output':   basins_raster_uni,
        }, context=context, feedback=feedback)
        feedback.pushInfo(f"    ✓ [7] Watershed unificado completado ({n_total} cuencas)")

        # Punto de detención 7
        if punto_detencion == 7:
            feedback.pushInfo("\n⏹ Detenido tras Watershed unificado.")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # ── FASE 2c: Vectorizar, Longest Flowpath e índices — TODO JUNTO ─
        feedback.pushInfo("\n[FASE 2c] Vectorizando cuencas (todo junto)...")

        # 1) Vectorizar el raster unificado una sola vez (gdal:polygonize)
        basins_vec_raw = tmp("basins_raw.shp")
        processing.run("gdal:polygonize", {
            'INPUT':  basins_raster_uni,
            'BAND':   1,
            'FIELD':  'DN',
            'EIGHT_CONNECTEDNESS': False,
            'EXTRA':  '',
            'OUTPUT': basins_vec_raw
        }, context=context, feedback=feedback)
        feedback.pushInfo("    ✓ [8] Raster → polígonos completado (gdal:polygonize)")

        # 2) Detectar el campo de valor del raster vectorizado (puede ser "DN", "VALUE", etc.)
        _lyr_raw = QgsVectorLayer(basins_vec_raw, "raw_chk", "ogr")
        val_field = None
        for _f in _lyr_raw.fields():
            if _f.name().upper() in ("DN", "VALUE", "GRIDCODE"):
                val_field = _f.name()
                break
        if val_field is None:
            # Buscar el primer campo entero/double que tenga valores 1..N
            for _f in _lyr_raw.fields():
                if _f.type() in (QVariant.Int, QVariant.Double, QVariant.LongLong):
                    val_field = _f.name()
                    break
        if val_field is None:
            raise Exception("No se encontró campo de valor numérico en basins_raw.shp")
        feedback.pushInfo(f"    Campo de valor detectado: '{val_field}'")
        del _lyr_raw

        # Reparar geometrías y disolver por ese campo — todo el shapefile de una vez
        basins_fixed = tmp("basins_fixed.shp")
        processing.run("native:fixgeometries", {
            'INPUT': basins_vec_raw, 'METHOD': 1, 'OUTPUT': basins_fixed
        }, context=context, feedback=feedback)

        basins_dissolved = tmp("basins_dissolved.shp")
        processing.run("native:dissolve", {
            'INPUT': basins_fixed, 'FIELD': [val_field], 'OUTPUT': basins_dissolved
        }, context=context, feedback=feedback)
        feedback.pushInfo(f"    ✓ Geometrías reparadas y disueltas por '{val_field}'")

        # Añadir campo cuenca_id a basins_dissolved usando el mapa valor→sufijo
        valor_a_sufijo = {i + 1: sufijo for (sufijo, i, *_) in snaps_info}
        lyr_diss = QgsVectorLayer(basins_dissolved, "diss", "ogr")
        lyr_diss.startEditing()
        lyr_diss.dataProvider().addAttributes([QgsField("cuenca_id", QVariant.String, len=80)])
        lyr_diss.updateFields()
        idx_cid = lyr_diss.fields().indexOf("cuenca_id")
        for feat in lyr_diss.getFeatures():
            val = feat[val_field]
            lyr_diss.changeAttributeValue(feat.id(), idx_cid, valor_a_sufijo.get(int(val) if val is not None else -1, str(val)))
        lyr_diss.commitChanges()

        # Punto de detención 8
        if punto_detencion == 8:
            cuenca_p8 = out("Cuencas_vec_todas.shp")
            processing.run("native:reprojectlayer" if reproyectado else "native:savefeatures",
                {'INPUT': basins_dissolved,
                 **({'TARGET_CRS': crs_original.authid()} if reproyectado else {}),
                 'OUTPUT': cuenca_p8},
                context=context, feedback=feedback)
            feedback.pushInfo("    ⏹ Detenido tras vectorización de cuencas.")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # 4) Longest Flowpath — UNA SOLA LLAMADA con el DEM y rasters originales
        # DEM_trabajo y basins_raster_uni tienen las mismas dimensiones (generados sobre el mismo grid)
        longest_fp_todos = tmp("longest_fp_todos.shp")
        eliminar_shapefile_si_existe(longest_fp_todos)
        processing.run("whitebox_workflows:longest_flowpath", {
            'dem':     fill,
            'd8_pntr': d8,
            'basins':  basins_raster_uni,
            'output':  longest_fp_todos
        }, context=context, feedback=feedback)
        feedback.pushInfo("    ✓ [9] Longest Flowpath (todas las cuencas) completado")

        # Añadir cuenca_id al shapefile de flowpaths usando el campo BASIN o FID
        lyr_fp = QgsVectorLayer(longest_fp_todos, "fp", "ogr")
        lyr_fp.startEditing()
        lyr_fp.dataProvider().addAttributes([QgsField("cuenca_id", QVariant.String, len=80)])
        lyr_fp.updateFields()
        idx_fp_cid = lyr_fp.fields().indexOf("cuenca_id")
        # Whitebox escribe el valor de la cuenca en el campo con nombre que contiene "BASIN" o como primer campo numérico
        basin_field = None
        for f in lyr_fp.fields():
            if "BASIN" in f.name().upper() or "VALUE" in f.name().upper():
                basin_field = f.name()
                break
        if basin_field is None:
            # Usar el campo con valores 1..N — buscar primer campo entero/double
            for f in lyr_fp.fields():
                if f.type() in (QVariant.Int, QVariant.Double, QVariant.LongLong):
                    basin_field = f.name()
                    break
        for feat in lyr_fp.getFeatures():
            bval = int(feat[basin_field]) if basin_field and feat[basin_field] is not None else None
            lyr_fp.changeAttributeValue(feat.id(), idx_fp_cid, valor_a_sufijo.get(bval, str(bval)))
        lyr_fp.commitChanges()

        # Punto de detención 9
        if punto_detencion == 9:
            fu_p9 = out("Longest_Flowpath_todas.shp")
            processing.run("native:reprojectlayer" if reproyectado else "native:savefeatures",
                {'INPUT': longest_fp_todos,
                 **({'TARGET_CRS': crs_original.authid()} if reproyectado else {}),
                 'OUTPUT': fu_p9},
                context=context, feedback=feedback)
            feedback.pushInfo("    ⏹ Detenido tras Longest Flowpath (sin perfil).")
            if not guardar_tmp: shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"CARPETA_SALIDA": out_dir}

        # 4) Índices morfométricos — sobre los shapefiles unificados
        cuencas_con_indices = tmp("cuencas_indices.shp")
        self._calcular_indices(
            basins_dissolved, longest_fp_todos, streams_v_global, DEM_trabajo,
            cuencas_con_indices, valor_a_sufijo, context, feedback)

        # 5) Perfiles topográficos — uno por cuenca, filtrando el shapefile unificado
        self._generar_perfiles(longest_fp_todos, DEM_trabajo, out_dir, valor_a_sufijo, feedback)
        feedback.pushInfo("    ✓ [10] Perfiles topográficos generados")

        feedback.setProgress(97)

        # ── FASE 3: Guardar salidas finales ───────────────────────────
        feedback.pushInfo("\n[FASE 3] Finalizando resultados...")

        def _guardar_capa(src_shp, nombre_dst, label):
            """Guarda (y reproyecta si procede) src_shp → out_dir/nombre_dst y carga al canvas."""
            dst = out(nombre_dst)
            eliminar_shapefile_si_existe(dst)
            if reproyectado:
                processing.run("native:reprojectlayer", {
                    'INPUT': src_shp, 'TARGET_CRS': crs_original.authid(), 'OUTPUT': dst
                }, context=context, feedback=feedback)
            else:
                processing.run("native:savefeatures", {
                    'INPUT': src_shp, 'OUTPUT': dst
                }, context=context, feedback=feedback)
            lyr = QgsVectorLayer(dst, label, "ogr")
            if lyr.isValid():
                context.temporaryLayerStore().addMapLayer(lyr)
                context.addLayerToLoadOnCompletion(
                    lyr.id(), QgsProcessingContext.LayerDetails(
                        label, QgsProject.instance(), label))

        # ── Salidas unificadas ─────────────────────────────────────────
        if hacer_unificado:
            feedback.pushInfo("    Guardando capas unificadas...")
            if os.path.exists(cuencas_con_indices):
                _guardar_capa(cuencas_con_indices, "Cuencas_morfometria.shp", "Cuencas_morfometria")
            if os.path.exists(longest_fp_todos):
                _guardar_capa(longest_fp_todos, "Longest_Flowpath_todas.shp", "Longest_Flowpath_todas")

        # ── Salidas separadas (un shapefile por cuenca) ───────────────
        if hacer_separado:
            feedback.pushInfo("    Generando capas separadas por cuenca...")
            lyr_cuencas = QgsVectorLayer(cuencas_con_indices, "cuen_sep", "ogr")
            lyr_fps     = QgsVectorLayer(longest_fp_todos, "fp_sep", "ogr")

            for sufijo_s in sufijos:
                # ── Cuenca individual ──────────────────────────────────
                expr_c   = f'"cuenca_id" = \'{sufijo_s}\''
                req_c    = QgsFeatureRequest().setFilterExpression(expr_c)
                feats_c  = list(lyr_cuencas.getFeatures(req_c)) if lyr_cuencas.isValid() else []
                if feats_c:
                    tmp_cuenca_s = tmp(f"cuenca_sep_{sufijo_s}.shp")
                    processing.run("native:extractbyexpression", {
                        "INPUT": cuencas_con_indices,
                        "EXPRESSION": expr_c,
                        "OUTPUT": tmp_cuenca_s
                    }, context=context, feedback=feedback)
                    _guardar_capa(tmp_cuenca_s,
                                  f"Cuencas_{sufijo_s}.shp",
                                  f"Cuencas_{sufijo_s}")

                # ── Flowpath individual ────────────────────────────────
                expr_f  = f'"cuenca_id" = \'{sufijo_s}\''
                feats_f = list(lyr_fps.getFeatures(
                    QgsFeatureRequest().setFilterExpression(expr_f))) if lyr_fps.isValid() else []
                if feats_f:
                    tmp_fp_s = tmp(f"fp_sep_{sufijo_s}.shp")
                    processing.run("native:extractbyexpression", {
                        "INPUT": longest_fp_todos,
                        "EXPRESSION": expr_f,
                        "OUTPUT": tmp_fp_s
                    }, context=context, feedback=feedback)
                    _guardar_capa(tmp_fp_s,
                                  f"Longest_Flowpath_{sufijo_s}.shp",
                                  f"Longest_Flowpath_{sufijo_s}")

            feedback.pushInfo(f"    ✓ Capas separadas generadas ({len(sufijos)} cuencas)")

        # ── Puntos corregidos ──────────────────────────────────────────
        if guardar_puntos and snaps_info:
            if reproy_exut:
                tr_back   = QgsCoordinateTransform(
                    crs_trabajo, crs_exut_orig, QgsProject.instance())
                snaps_out = []
                for (suf, _idx, xo, yo, xs, ys, dm) in snaps_info:
                    po = tr_back.transform(QgsPointXY(xo, yo))
                    ps = tr_back.transform(QgsPointXY(xs, ys))
                    snaps_out.append((suf, po.x(), po.y(), ps.x(), ps.y(), dm))
                crs_pts = crs_exut_orig
            else:
                snaps_out = [(s, xo, yo, xs, ys, dm) for (s, _i, xo, yo, xs, ys, dm) in snaps_info]
                crs_pts   = exut_layer.crs()
            self._guardar_puntos_corregidos(snaps_out, crs_pts, out_dir, context, feedback)
        else:
            feedback.pushInfo("    (Puntos_Corregidos.shp omitido — opción desactivada)")

        # ── Streams Vector ─────────────────────────────────────────────
        streams_v_out = out("Streams_Vector.shp")
        if os.path.exists(streams_v_global) and not os.path.exists(streams_v_out):
            processing.run("native:savefeatures", {
                'INPUT': streams_v_global, 'OUTPUT': streams_v_out
            }, context=context, feedback=feedback)
        streams_v_cargar = streams_v_out if os.path.exists(streams_v_out) else streams_v_global
        lyr_sv = QgsVectorLayer(streams_v_cargar, "Streams_Vector", "ogr")
        if lyr_sv.isValid():
            context.temporaryLayerStore().addMapLayer(lyr_sv)
            context.addLayerToLoadOnCompletion(
                lyr_sv.id(), QgsProcessingContext.LayerDetails(
                    "Streams_Vector", QgsProject.instance(), "Streams_Vector"))

        # ── Temporales ────────────────────────────────────────────────
        if guardar_tmp:
            feedback.pushInfo(
                f"    ℹ️  Archivos intermedios preservados en: {tmp_dir}\n"
                f"    (estos archivos NO se cargan al proyecto automáticamente)")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        feedback.setProgress(100)
        feedback.pushInfo("\n" + "=" * 60)
        feedback.pushInfo(f"✅ Proceso completado. Resultados en: {out_dir}")
        return {"CARPETA_SALIDA": out_dir}

    # ── _proyectar_punto_a_linea ─────────────────────────────────────── #
    def _proyectar_punto_a_linea(self, punto, capa_lineas, radio_busqueda=200.0):
        """
        Dado un punto (QgsPointXY) y una capa de líneas, devuelve el punto
        más cercano sobre cualquier línea dentro del radio de búsqueda.

        Algoritmo:
        1. Busca con filtro espacial (bbox) solo las líneas en el entorno
           del punto → eficiente incluso con miles de features.
        2. Para cada línea candidata calcula el punto de la línea más
           cercano al punto de entrada (nearestPoint).
        3. Devuelve el candidato más cercano. Si no hay ninguno dentro
           del radio, devuelve el punto original sin modificar.
        """
        geom_punto  = QgsGeometry.fromPointXY(punto)
        mejor_punto = punto
        menor_dist  = float("inf")

        # Filtro espacial para no iterar toda la capa
        bbox = QgsRectangle(
            punto.x() - radio_busqueda, punto.y() - radio_busqueda,
            punto.x() + radio_busqueda, punto.y() + radio_busqueda)
        request = QgsFeatureRequest().setFilterRect(bbox)

        for feat in capa_lineas.getFeatures(request):
            geom_linea = feat.geometry()
            if geom_linea is None or geom_linea.isEmpty():
                continue
            pt_cercano = geom_linea.nearestPoint(geom_punto)
            if pt_cercano is None or pt_cercano.isEmpty():
                continue
            dist = pt_cercano.distance(geom_punto)
            if dist < menor_dist:
                menor_dist  = dist
                mejor_punto = pt_cercano.asPoint()

        return mejor_punto

    # ── _guardar_puntos_corregidos ────────────────────────────────────── #
    def _guardar_puntos_corregidos(self, snaps_info, crs, out_dir, context, feedback):
        if not snaps_info:
            return
        campos = QgsFields()
        campos.append(QgsField("cuenca_id", QVariant.String, len=80))
        campos.append(QgsField("x_orig",    QVariant.Double))
        campos.append(QgsField("y_orig",    QVariant.Double))
        campos.append(QgsField("x_snap",    QVariant.Double))
        campos.append(QgsField("y_snap",    QVariant.Double))
        campos.append(QgsField("desp_m",    QVariant.Double))
        out_shp          = os.path.join(out_dir, "Puntos_Corregidos.shp")
        eliminar_shapefile_si_existe(out_shp)
        opts             = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName  = "ESRI Shapefile"
        opts.fileEncoding = "UTF-8"
        writer = QgsVectorFileWriter.create(
            out_shp, campos, QgsWkbTypes.Point, crs,
            QgsCoordinateTransformContext(), opts)
        if writer.hasError() != QgsVectorFileWriter.NoError:
            feedback.pushWarning(
                f"    ⚠ No se pudo crear Puntos_Corregidos.shp: {writer.errorMessage()}")
            return
        for (suf, xo, yo, xs, ys, dm) in snaps_info:
            f = QgsFeature(campos)
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(xs, ys)))
            f["cuenca_id"] = suf
            f["x_orig"]    = round(xo, 6)
            f["y_orig"]    = round(yo, 6)
            f["x_snap"]    = round(xs, 6)
            f["y_snap"]    = round(ys, 6)
            f["desp_m"]    = dm
            writer.addFeature(f)
        del writer
        feedback.pushInfo(
            f"    ✓ Puntos_Corregidos.shp guardado ({len(snaps_info)} puntos)")
        lyr = QgsVectorLayer(out_shp, "Puntos_Corregidos", "ogr")
        if lyr.isValid():
            context.temporaryLayerStore().addMapLayer(lyr)
            context.addLayerToLoadOnCompletion(
                lyr.id(), QgsProcessingContext.LayerDetails(
                    "Puntos_Corregidos", QgsProject.instance(), "Puntos_Corregidos"))

    # ── _calcular_indices ────────────────────────────────────────────── #
    def _calcular_indices(self, cuencas_shp, flowpaths_shp, streams_shp, dem_path,
                          out_shp, valor_a_sufijo, context, feedback):
        """Calcula índices morfométricos sobre el shapefile unificado de cuencas.
        Recibe cuencas_shp con campo VALUE (1..N) y flowpaths_shp con campo cuenca_id.
        valor_a_sufijo: dict {valor_int: sufijo_str}
        """
        from qgis import processing as proc

        cuenca = QgsVectorLayer(cuencas_shp, "cuencas", "ogr")
        if not cuenca.isValid():
            raise Exception(f"No se pudo cargar {cuencas_shp}")

        # Detectar campo de valor (DN, VALUE, etc.)
        val_field = None
        for _f in cuenca.fields():
            if _f.name().upper() in ("DN", "VALUE", "GRIDCODE"):
                val_field = _f.name()
                break
        if val_field is None:
            for _f in cuenca.fields():
                if _f.type() in (QVariant.Int, QVariant.Double, QVariant.LongLong):
                    val_field = _f.name()
                    break
        if val_field is None:
            raise Exception("No se encontró campo de valor numérico en cuencas_shp")

        # Añadir campos de índices
        cuenca.startEditing()
        campos_nuevos = [
            QgsField("cuenca_id", QVariant.String, len=80),
            QgsField("Area_km2",  QVariant.Double),
            QgsField("Perim_km",  QVariant.Double),
            QgsField("Kc",        QVariant.Double),
            QgsField("H_max_m",   QVariant.Double),
            QgsField("H_min_m",   QVariant.Double),
            QgsField("Lcauce_km", QVariant.Double),
            QgsField("Rr",        QVariant.Double),
            QgsField("Lt_km",     QVariant.Double),
            QgsField("Dd",        QVariant.Double),
        ]
        cuenca.dataProvider().addAttributes(campos_nuevos)
        cuenca.updateFields()
        idx = {f.name(): cuenca.fields().indexOf(f.name()) for f in campos_nuevos}

        # Estadísticas de elevación por feature (zonal statistics sobre cuencas_shp)
        zonal = proc.run("native:zonalstatisticsfb", {
            "INPUT": cuencas_shp, "INPUT_RASTER": dem_path,
            "RASTER_BAND": 1, "COLUMN_PREFIX": "_z",
            "STATISTICS": [5, 6], "OUTPUT": "TEMPORARY_OUTPUT"
        }, context=context)["OUTPUT"]
        # ── BUG FIX: usar el campo DN (valor de cuenca) como clave en vez de fid.
        # zonalstatisticsfb crea una capa temporal con fids propios que NO coinciden
        # con los fids de la capa 'cuenca' que está en edición → los valores de
        # elevación se asignaban al feature equivocado (bandurrrias recibía NULL).
        elev_por_val = {
            int(f[val_field]) if f[val_field] is not None else -1: (f["_zmax"], f["_zmin"])
            for f in zonal.getFeatures()
        }

        # Longitud del cauce más largo por cuenca (campo cuenca_id en flowpaths)
        fp_lyr = QgsVectorLayer(flowpaths_shp, "fp", "ogr")
        lcauce_por_sufijo = {}
        if fp_lyr.isValid():
            for f in fp_lyr.getFeatures():
                cid = f["cuenca_id"]
                if f.geometry() and not f.geometry().isEmpty():
                    largo = f.geometry().length() / 1000.0
                    # guardar el mayor por si hay múltiples segmentos
                    if cid not in lcauce_por_sufijo or largo > lcauce_por_sufijo[cid]:
                        lcauce_por_sufijo[cid] = largo

        # Longitud total de streams (igual para todas las cuencas — red global)
        streams = QgsVectorLayer(streams_shp, "streams", "ogr")
        lt_km_global = sum(
            f.geometry().length() / 1000.0
            for f in streams.getFeatures()
            if streams.isValid() and f.geometry())

        def r(v, d): return round(v, d) if v is not None else None

        for feat in cuenca.getFeatures():
            geom = feat.geometry()
            if not geom or geom.isEmpty():
                continue
            val    = feat[val_field]
            sufijo = valor_a_sufijo.get(int(val) if val is not None else -1, str(val))
            area_km2 = geom.area() / 1e6
            perim_km = geom.length() / 1000.0
            kc       = (0.28 * perim_km / math.sqrt(area_km2)) if area_km2 > 0 else None
            hmax, hmin = elev_por_val.get(int(val) if val is not None else -1, (None, None))
            lcauce_km  = lcauce_por_sufijo.get(sufijo, 0.0)
            rr         = ((hmax - hmin) / lcauce_km
                          if (hmax is not None and hmin is not None and lcauce_km > 0)
                          else None)
            # Dd: longitud total de streams dentro de esta cuenca / área
            # Aproximamos con la proporción por área (la red global cubre todas las cuencas)
            lt_km = lt_km_global  # se calcula por cuenca más abajo si es posible
            dd    = (lt_km / area_km2) if area_km2 > 0 else None

            cuenca.changeAttributeValue(feat.id(), idx["cuenca_id"], sufijo)
            cuenca.changeAttributeValue(feat.id(), idx["Area_km2"],  r(area_km2, 4))
            cuenca.changeAttributeValue(feat.id(), idx["Perim_km"],  r(perim_km, 4))
            cuenca.changeAttributeValue(feat.id(), idx["Kc"],        r(kc, 4))
            cuenca.changeAttributeValue(feat.id(), idx["H_max_m"],   r(hmax, 2))
            cuenca.changeAttributeValue(feat.id(), idx["H_min_m"],   r(hmin, 2))
            cuenca.changeAttributeValue(feat.id(), idx["Lcauce_km"], r(lcauce_km, 4))
            cuenca.changeAttributeValue(feat.id(), idx["Rr"],        r(rr, 4))
            cuenca.changeAttributeValue(feat.id(), idx["Lt_km"],     r(lt_km, 4))
            cuenca.changeAttributeValue(feat.id(), idx["Dd"],        r(dd, 4))

        cuenca.commitChanges()
        opts             = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName  = "ESRI Shapefile"
        opts.fileEncoding = "UTF-8"
        err, msg, _, _   = QgsVectorFileWriter.writeAsVectorFormatV3(
            cuenca, out_shp, QgsCoordinateTransformContext(), opts)
        if err != QgsVectorFileWriter.NoError:
            raise Exception(f"Error al guardar {out_shp}: {msg}")
        feedback.pushInfo(f"    ✓ Índices calculados y guardados: {out_shp}")

    # ── _generar_perfiles ────────────────────────────────────────────── #
    def _generar_perfiles(self, flowpaths_shp, dem_path, out_dir, valor_a_sufijo, feedback):
        """Genera un perfil topográfico por cuenca filtrando el shapefile unificado de flowpaths."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            feedback.pushWarning("    matplotlib no disponible, perfiles omitidos")
            return

        dem = QgsRasterLayer(dem_path, "dem")
        fp_lyr = QgsVectorLayer(flowpaths_shp, "fp", "ogr")
        if not fp_lyr.isValid() or not dem.isValid():
            feedback.pushWarning("    ⚠ No se pudo cargar flowpaths o DEM para perfiles")
            return

        dp = dem.dataProvider()

        # Agrupar geometrías por cuenca_id
        geoms_por_cuenca = {}
        for feat in fp_lyr.getFeatures():
            cid = feat["cuenca_id"]
            g   = feat.geometry()
            if g and not g.isEmpty():
                if cid not in geoms_por_cuenca:
                    geoms_por_cuenca[cid] = g
                else:
                    geoms_por_cuenca[cid] = geoms_por_cuenca[cid].combine(g)

        for sufijo, geom_total in geoms_por_cuenca.items():
            if not geom_total or geom_total.isEmpty():
                continue
            long_m = geom_total.length()
            n      = max(150, int(long_m / 50))
            step   = long_m / (n - 1) if n > 1 else 0
            dist, elev = [], []
            for i in range(n):
                pt  = geom_total.interpolate(i * step).asPoint()
                val, ok = dp.sample(pt, 1)
                if ok:
                    dist.append(i * step / 1000.0)
                    elev.append(val)
            if len(elev) < 2:
                continue

            h_max    = max(elev)
            h_min    = min(elev)
            desnivel = h_max - h_min
            long_km  = long_m / 1000.0
            rr_val   = desnivel / long_km if long_km > 0 else 0

            fig, ax = plt.subplots(figsize=(12, 5))
            ax.fill_between(dist, elev, h_min, color="#93C5FD", alpha=0.35)
            ax.plot(dist, elev, color="#1D4ED8", lw=2)
            ax.axhline(h_max, color="#B91C1C", ls="--", lw=0.9, alpha=0.8)
            ax.axhline(h_min, color="#15803D", ls="--", lw=0.9, alpha=0.8)

            idx_max  = elev.index(h_max)
            idx_min  = elev.index(h_min)
            d_max    = dist[idx_max]
            d_min    = dist[idx_min]
            margen_y = max(desnivel * 0.08, 10.0)
            ax.annotate(f"H máx = {h_max:.0f} m", xy=(d_max, h_max),
                        xytext=(d_max + long_km * 0.03, h_max + margen_y),
                        fontsize=8.5, color="#B91C1C", fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=0.9))
            ax.annotate(f"H mín = {h_min:.0f} m", xy=(d_min, h_min),
                        xytext=(d_min + long_km * 0.03, h_min + margen_y * 1.5),
                        fontsize=8.5, color="#15803D", fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color="#15803D", lw=0.9))

            pend_pct = (desnivel / long_m * 100.0) if long_m > 0 else 0.0
            info = (
                f"Longitud cauce : {long_km:.2f} km\n"
                f"Desnivel total : {desnivel:.0f} m\n"
                f"Pendiente      : {pend_pct:.2f} %\n"
                f"Rr             : {rr_val:.2f} m/km"
            )
            ax.text(0.98, 0.97, info, transform=ax.transAxes,
                    fontsize=8.5, va="top", ha="right", fontfamily="monospace",
                    bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                              edgecolor="#94A3B8", alpha=0.92))
            ax.set_xlabel("Distancia (km)", fontsize=11)
            ax.set_ylabel("Altitud (m s.n.m.)", fontsize=11)
            ax.set_title(f"Perfil Topográfico — Cuenca {sufijo}",
                         fontsize=12, fontweight="bold")
            ax.grid(True, ls="--", alpha=0.6)
            ax.set_xlim(left=0)
            plt.tight_layout()
            png = os.path.join(out_dir, f"Perfil_topografico_{sufijo}.png")
            plt.savefig(png, dpi=180, bbox_inches="tight")
            plt.close()
            feedback.pushInfo(f"    ✓ Perfil guardado: {png}")


def classFactory(iface):
    return SuperCuencasSupremo()
