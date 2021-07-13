# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IceVolume
                                 A QGIS plugin
 This plugin subtracts riverbed DEM from Ice surface DEM to estimate ice volume
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-09
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Einar Rødtang
        email                : einar.rodtang@protonmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .ice_volume_dialog import IceVolumeDialog
import os.path
import os
import sys
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry



class IceVolume:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'IceVolume_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Ice Volume')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('IceVolume', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/ice_volume/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Estimate ice parameters'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Ice Volume'),
                action)
            self.iface.removeToolBarIcon(action)
    
    def select_DEM_folder(self):
        foldername = QFileDialog.getExistingDirectory(self.dlg, "Choose DEM Folder")
        self.dlg.DEMFolderLineEdit.setText(foldername)
    
    def select_river_polygon(self):
        filename, _filter = QFileDialog.getOpenFileName(
        self.dlg, "Select river polygon","", '*.shp')
        self.dlg.riverPolygonLineEdit.setText(filename)
    
    def select_river_bed_DEM(self):
        filename, _filter = QFileDialog.getOpenFileName(
        self.dlg, "Select river bed DEM","", '*.tif')
        self.dlg.riverBedDEMLineEdit.setText(filename)
    
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = IceVolumeDialog()
            self.dlg.DEMFolderPushButton.clicked.connect(self.select_DEM_folder)
            self.dlg.riverPolygonPushButton.clicked.connect(self.select_river_polygon)
            self.dlg.riverBedDEMPushButton.clicked.connect(self.select_river_bed_DEM)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            Root_folder_path = self.dlg.DEMFolderLineEdit.text()
            No_ice_raster_path = self.dlg.riverBedDEMLineEdit.text()
            river_polygon_path = self.dlg.riverPolygonLineEdit.text()
            here = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(here)
            import Ice_thickness_estimation_script
            Ice_thickness_estimation_script.ice_thickness_estimator(Root_folder_path, No_ice_raster_path, river_polygon_path)
