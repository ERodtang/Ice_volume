import processing
from processing.core.Processing import Processing
import os
from os import *
import qgis
from  qgis.core import *

#These paths and files must be specified correctly by the user:
#############################################################
Root_folder_path = 'B:/QGIS_Drone_ice_vol/'                 # You need to specify the root folder of your project
No_ice_raster_name = '2020_10_06_Soknedals_tunnel_DEM.tif'  # Specify which DEM (in the DEM folder) that corresponds to the no ice condition (As low discharge as possible)
river_polygon_name = 'river_bank.shp'                       # Specify the name of a shape file that contains a polygon that covers the river, must be in project root directory
#############################################################
root = QgsProject.instance().layerTreeRoot()

DEM_folder_path = Root_folder_path + 'DEM/'                 # The root folder of your project must contain a folder called DEM containing your digital elevation models
river_polygon = QgsVectorLayer(Root_folder_path + river_polygon_name, 'river_polygon')
root.addLayer(river_polygon)
No_ice_raster_path = DEM_folder_path + No_ice_raster_name

#Initialise folder structure
CLIPPED_DEM_folder_path = Root_folder_path + 'CLIPPED_DEM/'
if os.path.isdir(CLIPPED_DEM_folder_path) == False: 
    os.mkdir(CLIPPED_DEM_folder_path)

DIFFERENCE_DEM_folder_path = Root_folder_path + 'DIFFERENCE_DEM/'
if os.path.isdir(DIFFERENCE_DEM_folder_path) == False:
    os.mkdir(DIFFERENCE_DEM_folder_path)

STATS_folder_path = Root_folder_path + 'STATS/'
if os.path.isdir(STATS_folder_path) == False:
    os.mkdir(STATS_folder_path)

#Initialise QGIS group structure
if QgsLayerTreeGroup.findGroup(root,'DEM') == NULL:
    QgsLayerTreeGroup.addGroup(root,'DEM')

if QgsLayerTreeGroup.findGroup(root,'CLIPPED_DEM') == NULL:
    QgsLayerTreeGroup.addGroup(root,'CLIPPED_DEM')

if QgsLayerTreeGroup.findGroup(root,'DIFFERENCE_DEM') == NULL:
    QgsLayerTreeGroup.addGroup(root,'DIFFERENCE_DEM')

if QgsLayerTreeGroup.findGroup(root,'STATS') == NULL:
    QgsLayerTreeGroup.addGroup(root,'STATS')

DEM_group = QgsLayerTreeGroup.findGroup(root,'DEM')
DIFFERENCE_DEM_group = QgsLayerTreeGroup.findGroup(root,'DIFFERENCE_DEM')
CLIPPED_DEM_group = QgsLayerTreeGroup.findGroup(root,'CLIPPED_DEM')
STATS_group = QgsLayerTreeGroup.findGroup(root,'STATS')

No_ice_CLIPPED_raster_path = CLIPPED_DEM_folder_path + No_ice_raster_name
No_ice_CLIPPED_raster_path = No_ice_CLIPPED_raster_path.removesuffix('DEM.tif')+'CLIPPED_DEM.tif'

#Add all DEM files to Qgis canvas
for root, dirs, files in os.walk(DEM_folder_path):
    for name in files:
        DEM_full_path = root + name
        DEM_layer_name = name
        DEM_layer_name = DEM_layer_name.removesuffix('.tif')
        DEM_layer = QgsRasterLayer(DEM_full_path,DEM_layer_name)
        #Only add to canvas if layer doesn't already exist
        if len(QgsProject.instance().mapLayersByName(DEM_layer_name)) == 0:
            QgsProject.instance().addMapLayer(DEM_layer, False)
            DEM_group.addLayer(DEM_layer)
        else:
            print("Tried to add layer " + DEM_layer_name + ", however layer already in canvas. Hence layer not added")

#Clip rasters to river extent
for layer in DEM_group.findLayers():
    ras = QgsRasterLayer(str(DEM_folder_path)+str(layer.name())+'.tif')
    output_string = str(CLIPPED_DEM_folder_path)+str(layer.name())
    output_string = output_string.removesuffix('DEM')+'CLIPPED_DEM.tif'
    parameters = {'INPUT': ras,
    'MASK': river_polygon,
    'NODATA': -9999,
    'ALPHA_BAND': False,
    'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': True,
    'OPTIONS': None,
    'DATA_TYPE': 0,
    'OUTPUT': output_string}
    processing_results = processing.run('gdal:cliprasterbymasklayer', parameters)
    CLIPPED_layer_name = str(layer.name()).removesuffix('DEM')+'CLIPPED_DEM'
    CLIPPED_layer = QgsRasterLayer(output_string, CLIPPED_layer_name)
    #Only add to canvas if layer doesn't already exist
    if len(QgsProject.instance().mapLayersByName(CLIPPED_layer_name)) == 0:
        QgsProject.instance().addMapLayer(CLIPPED_layer, False)
        CLIPPED_DEM_group.addLayer(CLIPPED_layer)
    else:
        print("Tried to add layer " + CLIPPED_layer_name + ", however layer already in canvas. Hence layer not added")


#Subtract rasters from no ice raster
no_ice_layer = QgsRasterLayer(No_ice_CLIPPED_raster_path)
no_ice_ras = QgsRasterCalculatorEntry()
no_ice_ras.ref = 'no_ice_ras@1'
no_ice_ras.raster = no_ice_layer
no_ice_ras.bandNumber = 1
ras={} #Initialize raster dictionary
for layer in CLIPPED_DEM_group.findLayers():
    entries = []
    entries.append(no_ice_ras)
    lyr1 = QgsRasterLayer(str(CLIPPED_DEM_folder_path)+str(layer.name())+'.tif')
    output = str(DIFFERENCE_DEM_folder_path)+str(layer.name())
    output = output.removesuffix('CLIPPED_DEM')+'DIFFERENCE_DEM.tif'
    ras[(str(layer.name())+'_ras')] = QgsRasterCalculatorEntry()
    ras[(str(layer.name())+'_ras')].ref = str(layer.name())+'@1'
    ras[(str(layer.name())+'_ras')].raster = lyr1
    ras[(str(layer.name())+'_ras')].bandNumber = 1
    entries.append(ras[(str(layer.name())+'_ras')])
    computation_str = str(ras[(str(layer.name())+'_ras')].ref + ' - no_ice_ras@1')
    calc = QgsRasterCalculator(computation_str, output, 'GTiff', lyr1.extent(), lyr1.width() ,lyr1.height(),entries)
    calc.processCalculation()
    DIFFERENCE_layer_name = layer.name()
    DIFFERENCE_layer_name = DIFFERENCE_layer_name.removesuffix('CLIPPED_DEM')+'DIFFERENCE_DEM'
    DIFFERENCE_layer = QgsRasterLayer(output,DIFFERENCE_layer_name)
    #Only add to canvas if layer doesn't already exist
    if len(QgsProject.instance().mapLayersByName(DIFFERENCE_layer_name)) == 0:
        QgsProject.instance().addMapLayer(DIFFERENCE_layer, False)
        DIFFERENCE_DEM_group.addLayer(DIFFERENCE_layer)
    else:
        print("Tried to add layer " + DIFFERENCE_layer_name + ", however layer already in canvas. Hence layer not added")


#Calculate raster statistics
for layer in DIFFERENCE_DEM_group.findLayers():
    current_DEM = DIFFERENCE_DEM_folder_path+layer.name()+'.tif'
    current_OUTPUT = STATS_folder_path + layer.name()
    current_OUTPUT = current_OUTPUT.removesuffix('DIFFERENCE_DEM')+"STATS.shp"
    column_prefix = '_'
    if(os.path.isfile(current_OUTPUT) == False):
        parameters = {'COLUMN_PREFIX' : column_prefix, 
        'INPUT' : river_polygon, 
        'INPUT_RASTER' : current_DEM, 
        'OUTPUT' : current_OUTPUT, 
        'RASTER_BAND' : 1,
        'STATISTICS' : [1,2,3,4,5,6]}
        processing_results = processing.run("native:zonalstatisticsfb", parameters)
        STATS_layer_name = str(layer.name()).removesuffix('DIFFERENCE_DEM')+'STATS'
        STATS_layer = QgsVectorLayer(processing_results['OUTPUT'], STATS_layer_name)
        #Only add to canvas if layer doesn't already exist
        if len(QgsProject.instance().mapLayersByName(STATS_layer_name)) == 0:
            QgsProject.instance().addMapLayer(STATS_layer, False)
            STATS_group.addLayer(STATS_layer)
        else:
            print("Tried to add layer " + STATS_layer_name + ", however layer already in canvas. Hence layer not added")
