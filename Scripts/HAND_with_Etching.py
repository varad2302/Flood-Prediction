# This scripts runs the terrain analysis steps to create the HAND map.

import arcpy
import os
import sys
import time

def main(in_dir, out_dir, dem_dir, hydrog_dir, info1, info2, info3, info4, info5, info6, info7, info8):
    arcpy.env.overwriteOutput = True

    # Create the output directory
    if not os.path.isdir(os.getcwd() + out_dir):
        os.makedirs(os.getcwd() + out_dir)

    # Step 1. Use "raster domain" tool from arcpy and create a domain shapefile from the DEM raster file.
    print("Start the pre-processing steps")
    arcpy.RasterDomain_3d(in_raster=os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1,
                          out_feature_class=os.getcwd()+out_dir + info2,
                          out_geometry_type="POLYGON")

    # Step 2. Select the domain shapefile and define an internal buffer of the domain shapefile using "buffer" tool.
    # Remember to use negative sign for the internal buffer. Here, we used 500 m for the Ocheyedan River case when using
    # 3 m DEM.
    arcpy.Buffer_analysis(in_features=os.getcwd()+out_dir + info2,
                          out_feature_class=os.getcwd()+out_dir + info3,
                          buffer_distance_or_field=info4,
                          line_side="FULL",
                          line_end_type="ROUND",
                          dissolve_option="NONE",
                          dissolve_field="",
                          method="GEODESIC")

    # Step 3. Use "select by attribute" tool to exclude the canals.
    name1 = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + hydrog_dir + info5
    name_temp1 = name1.replace('.shp', '_lyr')
    arcpy.MakeFeatureLayer_management(name1, name_temp1)
    medres_NHDPlusflowline_noCanal = arcpy.SelectLayerByAttribute_management(name_temp1, 'NEW_SELECTION',
                                                                             "FTYPE <> " + info7)

    name2 = os.getcwd()+in_dir + info6
    name_temp2 = name2.replace('.shp', '_lyr')
    arcpy.MakeFeatureLayer_management(name2, name_temp2)
    arcpy.SelectLayerByAttribute_management(name_temp2, 'NEW_SELECTION', "FTYPE <> " + info8)
    arcpy.CopyFeatures_management(name_temp2, os.getcwd() + out_dir + 'highres_NHDPlusflowline_noCanal.shp')


    # Step 4. Clip the medium for the "internal500mbuffer.shp". Note the the high resolution should be also clipped
    # for the "internal500mbuffer.shp" except for making sure that the last segment (following the flow path)
    # leaves the domain. We have done this part in ArcGIS software and we provided the clipped high resolution with the
    # mentioned condition in the Input directory to be used for reproducing the results.
    arcpy.Clip_analysis(in_features=medres_NHDPlusflowline_noCanal,
                        clip_features=os.getcwd()+out_dir + info3,
                        out_feature_class=os.getcwd()+out_dir + 'medres_NHDPlusflowline_noCanal_to_bfr.shp',
                        cluster_tolerance="")

    # Step 5. Find the starting points (dangles) that are used as an input to the network delineation process.
    #         In this research study, we used the main stems for the dangles. This was done within the ArcGIS software
    #         and the results are here as input files for the next steps. Following comment explains the steps we took
    #         in the ArcGIS software to create these files.

    #         1.Select the dangles (using "feature vertices to points" tool and set point_location="DANGLE").
    #         These are going to be used as the starting points to delineate the stream network. In our work, we only
    #         considered the main stems when generating the dangle points. This is due to the fact that the main stems
    #         had larger contributing areas in our case studies compared to the side tributaries.

    #         2.Open the attribute table of the dangle shapefile. Add a field using "add field" tool. Then, use
    #         "calculate field" tool to put a value of 1 for all the rows in this field.

    #         3.Use "feature to raster" tool to rasterize the dangle points. Make sure to set the extent and snap
    #         raster sizes to be the same as the DEM size (an extracted DEM that covers the domain) in the enviroment
    #         settings of the tool.

    #         4.Use the "reclassify" tool to reclassify the inlets.tif raster layer so that 1 is one and the rest (
    #         i.e., 0 or NAN) is zero.

    # Step 6. Generate the evenly dispersed nodes along the main stem.
    #         The evenly dispersed nodes are used as an input to the network delineation process. This was done within
    #         the ArcGIS software and the results are here as input files for the next steps. Following comment explains
    #         the steps we took in the ArcGIS software to create these nodes.

    #         1.Select the main stem from the buffered medium resolution NHDPlus
    #         dataset and save it as a new feature. Then, use "dissolve" tool to merge the segments (reaches) of this
    #         new feature into one single segment. Next, use "editor -> split" tool to split this feature into smaller
    #         equal segments with 3 km long. Then, create a new point shapefile and use the editor tool to generate
    #         points on the upstream and downstream ends of these equal segments. The new shape file is the evenly
    #         dispersed nodes on the main stems. This is required when delineating the stream network and catchments.

    # Step 7. Creating a conditioned DEM and calculating the HAND the following procedure.

    # 1.Rasterize the high-resolution NHD since we want to burn them into the DEM. For that, use "polyline to raster"
    # tool. Do not forget to set the extent and snap raster resolution as the DEM in the environment settings.
    # Our application with high-resolution NHD streams has different classes of flowlines, specifically StreamRiver,
    # ArtificialPath, CanalDitch, Pipeline, Connector, Coastline, and Underground Conduit. We excluded all except
    # StreamRiver, ArtificialPath, and Pipeline/Connector and used B=1000 m for StreamRiver, 700 m for ArtificialPath,
    # and 400 m for Pipeline/Connector, which gives preference to flow along the StreamRiver line that we took to be
    # the main flow path in braided situations. Then, an ArtificialPath is prioritized over a Pipeline/Connector.

    print('Rasterize the high-resolution NHD')
    # PIPELINE or CONNECTOR
    name1 = os.getcwd()+out_dir + 'highres_NHDPlusflowline_noCanal.shp'
    name_temp1 = name1.replace('.shp', '_lyr')
    arcpy.MakeFeatureLayer_management(name1, name_temp1)
    highres_NHDPlusflowline_noCanal_pipelineconnector = arcpy.SelectLayerByAttribute_management(name_temp1,
                                                                                                'NEW_SELECTION',
                                                                                                "FTYPE = 428 OR FTYPE = 334")
    arcpy.env.extent = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    arcpy.env.snapRaster = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    arcpy.PolylineToRaster_conversion(in_features=highres_NHDPlusflowline_noCanal_pipelineconnector,
                                      value_field="FlowDir",
                                      out_rasterdataset=os.getcwd()+out_dir + "srfv1_pc.tif",
                                      cell_assignment="MAXIMUM_LENGTH",
                                      priority_field="NONE",
                                      cellsize=os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1)

    # ARTIFICIAL PATH
    name2 = os.getcwd()+out_dir + 'highres_NHDPlusflowline_noCanal.shp'
    name_temp2 = name2.replace('.shp', '_lyr')
    arcpy.MakeFeatureLayer_management(name2, name_temp2)
    highres_NHDPlusflowline_noCanal_artificialpath = arcpy.SelectLayerByAttribute_management(name_temp2,
                                                                                                'NEW_SELECTION',
                                                                                                "FTYPE = 558")
    arcpy.env.extent = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    arcpy.env.snapRaster = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    arcpy.PolylineToRaster_conversion(in_features=highres_NHDPlusflowline_noCanal_artificialpath,
                                      value_field="FlowDir",
                                      out_rasterdataset=os.getcwd()+out_dir + "srfv1_ap.tif",
                                      cell_assignment="MAXIMUM_LENGTH",
                                      priority_field="NONE",
                                      cellsize=os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1)

    # STREAM RIVER
    name3 = os.getcwd()+out_dir + 'highres_NHDPlusflowline_noCanal.shp'
    name_temp3 = name3.replace('.shp', '_lyr')
    arcpy.MakeFeatureLayer_management(name3, name_temp3)
    highres_NHDPlusflowline_noCanal_streamriver = arcpy.SelectLayerByAttribute_management(name_temp3,
                                                                                                'NEW_SELECTION',
                                                                                                "FTYPE = 460")
    arcpy.env.extent = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    arcpy.env.snapRaster = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    arcpy.PolylineToRaster_conversion(in_features=highres_NHDPlusflowline_noCanal_streamriver,
                                      value_field="FlowDir",
                                      out_rasterdataset=os.getcwd()+out_dir + "srfv1_sr.tif",
                                      cell_assignment="MAXIMUM_LENGTH",
                                      priority_field="NONE",
                                      cellsize=os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1)

    # 2.Reclassify the resulting raster to 1 on streams and 0 off streams.
    arcpy.gp.Reclassify_sa(os.getcwd()+out_dir + "srfv1_pc.tif",
                           "Value",
                           "0 0;1 1;NODATA 0",
                           os.getcwd()+out_dir + "srfv_pc.tif",
                           "DATA")
    arcpy.gp.Reclassify_sa(os.getcwd()+out_dir + "srfv1_ap.tif",
                           "Value",
                           "0 0;1 1;NODATA 0",
                           os.getcwd()+out_dir + "srfv_ap.tif",
                           "DATA")
    arcpy.gp.Reclassify_sa(os.getcwd()+out_dir + "srfv1_sr.tif",
                           "Value",
                           "0 0;1 1;NODATA 0",
                           os.getcwd()+out_dir + "srfv_sr.tif",
                           "DATA")

    # 3.Use the "raster calculator" tool to create a raster with the following argument: (original_dem) - (srfv.tif) * 1000
    print("Starting the burning process")
    arcpy.gp.RasterCalculator_sa('"'+os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1 + '"' +
                                 ' - 400 * ' + '"' + os.getcwd()+out_dir + "srfv_pc.tif" + '"' +
                                 ' - 700 * ' + '"' + os.getcwd()+out_dir + "srfv_ap.tif" + '"' +
                                 ' - 1000 * ' + '"' + os.getcwd()+out_dir + "srfv_sr.tif" + '"',
                                 os.getcwd()+out_dir + "zb.tif")

    # 4.Fill pits in the burned dem
    print('PitRemove the burned DEM')
    i_path = os.getcwd()+out_dir + "zb.tif"
    o_path = os.getcwd()+out_dir + "zbfel.tif"
    bashCommand = "mpiexec -n 10 PitRemove -z " + i_path + " -fel " + o_path
    os.system(bashCommand)
    time.sleep(120)

    # 5.Compute the D8 flow direction. This function may take several hours to run. This takes about 120 minutes to run.
    print('Running D8 Flow Direction Function for the pit removed burned DEM')
    i_path = os.getcwd()+out_dir + "zbfel.tif"
    o1_path = os.getcwd()+out_dir + "zbp.tif"
    o2_path = os.getcwd()+out_dir + "zbsd8.tif"
    bashCommand = "mpiexec -n 10 D8FlowDir -fel " + i_path + " -p " + o1_path + " -sd8 " + o2_path
    os.system(bashCommand)
    time.sleep(360)

    # 6.Mask the D8 flow direction only for streams using raster calculator
    # Note that in some cases, the pixel that connects two different types of flowlines gets the value of 1
    # in both rasterized datasets. This causes issue when summing the rasterized datasets and results in the value of
    # 2 for that pixel. Using the value of 2 will create a zbpm which has continuous values between 0-8. Not interger
    # values. To avoid this, we first sum the three rasterized flowline datasets and then do a simple reclassification.
    # Next, we will create zbpm.tif

    arcpy.gp.RasterCalculator_sa('"' + os.getcwd() + out_dir + "srfv_pc.tif" + '"' +
                                 ' + ' + '"' + os.getcwd() + out_dir + "srfv_ap.tif" + '"' +
                                 ' + ' + '"' + os.getcwd() + out_dir + "srfv_sr.tif" + '"',
                                 os.getcwd() + out_dir + "srfv_pc_ap_sr.tif")

    arcpy.gp.Reclassify_sa(os.getcwd() + out_dir + "srfv_pc_ap_sr.tif", "Value", "0 0;1 3 1;NODATA NODATA",
                           os.getcwd() + out_dir + "srfv_pc_ap_sr_Rc.tif", "DATA")

    arcpy.gp.RasterCalculator_sa('"' + os.getcwd() + out_dir + "zbp.tif" + '"' +
                                 ' / ' + '"' + os.getcwd() + out_dir + "srfv_pc_ap_sr_Rc.tif" + '"',
                                 os.getcwd() + out_dir + "zbpm.tif")


    # 7.Produce the flow direction conditioned dem using the "flowdircond" function of taudem.
    print('Running Flow Direction Conditioning Function to etch the high resolution NHD to the DEM')
    i1_path = os.path.normpath(os.getcwd()+os.sep+os.pardir+os.sep+os.pardir) + dem_dir + info1
    i2_path = os.getcwd()+out_dir + "zbpm.tif"
    o_path = os.getcwd()+out_dir + "zfdc.tif"
    bashCommand = "mpiexec -n 10 flowdircond -z " + i1_path + " -p " + i2_path + " -zfdc " + o_path
    os.system(bashCommand)

    # 8.Fill pits in the original dem
    print('Running PitRemove Function using the etched DEM')
    i_path = os.getcwd()+out_dir + "zfdc.tif"
    o_path = os.getcwd()+out_dir + "zfdcfel.tif"
    bashCommand = "mpiexec -n 10 PitRemove -z " + i_path + " -fel " + o_path
    os.system(bashCommand)
    time.sleep(300)

    # 9.Compute the D8 flow direction. This function may take several hours to run. This takes about 20 minutes to run.
    print('Running D8 Flow Direction Function for the pit removed etched DEM')
    i_path = os.getcwd()+out_dir + "zfdcfel.tif"
    o1_path = os.getcwd()+out_dir + "zfdcp.tif"
    o2_path = os.getcwd()+out_dir + "zfdcsd8.tif"
    bashCommand = "mpiexec -n 10 D8FlowDir -fel " + i_path + " -p " + o1_path + " -sd8 " + o2_path
    os.system(bashCommand)
    time.sleep(360)

    # 10.Compute D8 area contributing Compute D8 area contributing.
    print('Running D8 Area Contributing Function for the etched DEM')
    i1_path = os.getcwd()+in_dir + "inlets_on_mainstem.tif"
    i2_path = os.getcwd()+out_dir + "zfdcp.tif"
    o_path = os.getcwd()+out_dir + "zfdcad8.tif"
    bashCommand = "mpiexec -n 10 Aread8 -wg " + i1_path + " -p " + i2_path + " -ad8 " + o_path + " -nc "
    os.system(bashCommand)
    time.sleep(360)

    # 11.Use a threshold to delineate the stream
    print('Delineating the stream network and catchments')
    i_path = os.getcwd()+out_dir + "zfdcad8.tif"
    o_path = os.getcwd()+out_dir + "zfdcsrc.tif"
    bashCommand = "mpiexec -n 10 Threshold -ssa " + i_path + " -src " + o_path + " -thresh 1"
    os.system(bashCommand)

    # 12.Generate network and watershed
    i1_path = os.getcwd()+in_dir + "Evenly_dispersed_nodes.shp"
    i2_path = os.getcwd()+out_dir + "zfdcfel.tif"
    i3_path = os.getcwd()+out_dir + "zfdcp.tif"
    i4_path = os.getcwd()+out_dir + "zfdcad8.tif"
    i5_path = os.getcwd()+out_dir + "zfdcsrc.tif"
    o1_path = os.getcwd()+out_dir + "zfdcord.tif"
    o2_path = os.getcwd()+out_dir + "zfdctree.dat"
    o3_path = os.getcwd()+out_dir + "zfdccoord.dat"
    o4_path = os.getcwd()+out_dir + "zfdcnet.shp"
    o5_path = os.getcwd()+out_dir + "zfdcw.tif"
    bashCommand = "mpiexec -n 10 Streamnet -o " + i1_path + " -fel " + i2_path + " -p " + i3_path + \
                  " -ad8 " + i4_path + " -src " + i5_path + " -ord " + o1_path + " -tree " + o2_path + \
                  " -coord " + o3_path + " -net " + o4_path + " -w " + o5_path
    os.system(bashCommand)

    # 13.Compute the D-inf flow direction.
    print('Running D-infinity Flow Direction Function for the etched DEM')
    i_path = os.getcwd()+out_dir + "zfdcfel.tif"
    o1_path = os.getcwd()+out_dir + "zfdcang.tif"
    o2_path = os.getcwd()+out_dir + "zfdcslp.tif"
    bashCommand = "mpiexec -n 10 DinfFlowDir -fel " + i_path + " -ang " + o1_path + " -slp " + o2_path
    os.system(bashCommand)
    time.sleep(360)

    # # 14. Compute the HAND using D-inf Distance Down.
    print('Running D-infinity Distance Down Function to create HAND')
    i1_path = os.getcwd() + out_dir + "zfdcfel.tif"
    i2_path = os.getcwd() + out_dir + "zfdcsrc.tif"
    i3_path = os.getcwd() + out_dir + "zfdcang.tif"
    o_path = os.getcwd() + out_dir + "hand.tif"
    bashCommand = "mpiexec -n 10 DinfDistDown -fel " + i1_path + " -src " + i2_path + " -ang " + i3_path + " -m ave v " + " -dd " + o_path + " -nc "
    os.system(bashCommand)
    time.sleep(360)

    print('Done!')


if __name__ == '__main__':
    in_dir = sys.argv[1]
    out_dir = sys.argv[2]
    dem_dir = sys.argv[3]
    hydrog_dir = sys.argv[4]
    info1 = sys.argv[5]
    info2 = sys.argv[6]
    info3 = sys.argv[7]
    info4 = sys.argv[8]
    info5 = sys.argv[9]
    info6 = sys.argv[10]
    info7 = sys.argv[11]
    info8 = sys.argv[12]

    main(in_dir, out_dir, dem_dir, hydrog_dir, info1, info2, info3, info4, info5, info6, info7, info8)

