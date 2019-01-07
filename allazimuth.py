# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2018 Maciej Kamiński (kaminski.maciej@gmail.com) Politechnika Wrocławska
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
###############################################################################
__author__ = 'Maciej Kamiński Politechnika Wrocławska'
import os
from PyQt5.QtWidgets import QAction,QMessageBox,QApplication
from PyQt5.QtCore import Qt, QBasicTimer, QVariant
from PyQt5.QtGui import QIcon
from qgis.core import *
import math,cmath

class AllAzimuth(QAction):
    """
    Action for opening a widget
    """
    def __init__(self,plugin):
        self.plugin=plugin
        super(AllAzimuth,self).__init__(
			plugin.qicon,
			"Connect",
			plugin.iface.mainWindow()
			)
        self.triggered.connect(self.run)
        self.iface=plugin.iface
        # dailog cannot be set in function variable (it is GCed)
        self.dlg=None
        self.bestname="azimuth"

    def run(self):
        """
        Just show/dock Widget
        """
        self.dlg=self.plugin.ui_loader('main_window.ui')
        self.dlg.compute.clicked.connect(self.compute)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea,self.dlg)
        self.dlg.LayerComboQ.layerChanged.connect(self.layer_change)
        self.dlg.LayerComboQ.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.dlg.compute.setEnabled(False)
        self.layer_change()

    def compute(self):
        layer=self.dlg.LayerComboQ.currentLayer()
        column_name=self.dlg.colname.text()
        field = QgsField(column_name, QVariant.Int )
        dp=layer.dataProvider()
        dp.addAttributes([field])
        layer.updateFields()
        afi=dp.fields().indexOf(column_name)

        features=dp.getFeatures()
        geometries=list(map(lambda x:x.geometry(),features))
        ok_geometries=list(map(lambda x:x.convertToSingleType(),geometries))
        assert all(ok_geometries)
        sgeometries=list(map(lambda x:(x.asPolyline()[0],x.asPolyline()[-1]),geometries))
        azimuths=list(map(lambda x:self.azimuth(*x),sgeometries))
        azwc=list(map(lambda x:{afi:x},azimuths))
        ids=list(map(lambda x:x.id(),dp.getFeatures()))

        values_to_change=dict(zip(ids,azwc))
        dp.changeAttributeValues(values_to_change)
        layer.commitChanges()
        self.layer_change()

    def layer_change(self):
        if self.dlg.LayerComboQ.currentLayer():
            self.dlg.compute.setEnabled(True)
        else:
            self.dlg.compute.setEnabled(False)
            return
        suffix=""
        while not self.dlg.LayerComboQ.currentLayer().fields().indexOf(self.bestname+suffix)<0:
            suffix+="#"
        self.dlg.colname.setText(self.bestname+suffix)

    def azimuth(self,point_start,point_end):
                vstart=complex(*point_start)
                vend=complex(*point_end)
                vv=vend-vstart

                alpha=math.pi/2-cmath.phase(vv)
                if alpha<0:
                    alpha+=cmath.pi*2
                # to degrees
                degree=alpha/(cmath.pi*2)*360
                return int(degree)
