"""
Proveedor de Processing para el complemento Super Cuencas.

Registra el algoritmo SuperCuencasSupremo dentro del grupo
"Hidrología Avanzada" en la Caja de Herramientas de Procesos de QGIS.
"""

import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .super_cuencas_supremo import SuperCuencasSupremo


class SuperCuencasProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(SuperCuencasSupremo())

    def id(self):
        return "super_cuencas"

    def name(self):
        return "Super Cuencas"

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "super_cuencas_logo.png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return super().icon()

    def longName(self):
        return "Super Cuencas — Delimitación y análisis morfométrico de cuencas hidrográficas"
