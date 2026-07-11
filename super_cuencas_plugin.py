"""
Clase principal del complemento Super Cuencas.

QGIS llama a initGui() al activar el complemento y a unload() al
desactivarlo. Aquí solo se registra/retira el QgsProcessingProvider;
no se agrega ningún ítem de menú ni barra de herramientas porque
Super Cuencas se usa exclusivamente desde la Caja de Herramientas
de Procesos.
"""

from qgis.core import QgsApplication

from .super_cuencas_provider import SuperCuencasProvider


class SuperCuencasPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        self.provider = SuperCuencasProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
