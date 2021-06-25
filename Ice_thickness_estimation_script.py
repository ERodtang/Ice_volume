import processing
from processing.core.Processing import Processing

Root_folder_path = 'B:/QGIS_Drone_ice_vol/'                 # You need to specify the root folder of your project
No_ice_raster_name = '2020_12_16_Soknedals_tunnel_DEM.tif'  # Specify which DEM (in the DEM folder) that corresponds to the no ice condition (As low discharge as possible)
river_polygon_name = 'river_bank.shp'                       # Specify the name of a shape file that contains a polygon that covers the river, must be in project root directory
DEM_folder_path = Root_folder_path + 'DEM/'                 # The root folder of your project must contain a folder called DEM containing your digital elevation models
CLIPPED_DEM_folder_path = Root_folder_path + 'CLIPPED_DEM/'
if os.path.isdir(CLIPPED_DEM_folder_path) == False: 
    os.mkdir(CLIPPED_DEM_folder_path)

DIFFERENCE_DEM_folder_path = Root_folder_path + 'DIFFERENCE_DEM/'
if os.path.isdir(DIFFERENCE_DEM_folder_path) == False:
    os.mkdir(DIFFERENCE_DEM_folder_path)

No_ice_raster_path = DEM_folder_path + No_ice_raster_name
No_ice_raster_path = No_ice_raster_path.removesuffix('DEM')+'CLIPPED_DEM.tif'
river_polygon = QgsVectorLayer(Root_folder_path + river_polygon_name)
root = QgsProject.instance().layerTreeRoot()#Make a layer tree

#Clip rasters to river extent
for layer in root.children():
    if layer.name().endswith('tunnel_DEM'):
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
        processing.runAndLoadResults('gdal:cliprasterbymasklayer', parameters)

#Subtract rasters from no ice raster
no_ice_layer = QgsRasterLayer(No_ice_raster_path)
no_ice_ras = QgsRasterCalculatorEntry()
no_ice_ras.ref = 'no_ice_ras@1'
no_ice_ras.raster = no_ice_layer
no_ice_ras.bandNumber = 1
ras={} #Initialize raster dictionary
for layer in root.children():
    if layer.name().endswith('CLIPPED_DEM'):
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
        computation_str = str('no_ice_ras@1 - '+ras[(str(layer.name())+'_ras')].ref)
        calc = QgsRasterCalculator(computation_str, output, 'GTiff', lyr1.extent(), lyr1.width() ,lyr1.height(),entries)
        calc.processCalculation()

