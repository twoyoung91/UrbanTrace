# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 13:41:36 2024

@author: Yang Yang
"""

# mainPlugin.py
# -*- coding: utf-8 -*-

#load the necessary libraries
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer
from .dialog import YoloPredDialog
import os
import rasterio
import numpy as np
import pandas as pd
from shapely.geometry import box
import geopandas as gpd
from itertools import product
from shapely.geometry import Polygon
import torch

#load submodules
import detection

class urbanTrace:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        self.model_path = os.path.join(self.plugin_dir,"detection.pt") 
        self.modelset = "_combined_det"
        self.model = None

    def initGui(self):
        self.action = QAction("UrbanTrace Building Detection", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&UrbanTrace", self.action)

        self.iface.mapCanvas().renderComplete.connect(self.renderTest)

    def unload(self):
        self.iface.removePluginMenu("&UrbanTrace", self.action)
        self.iface.removeToolBarIcon(self.action)
        self.iface.mapCanvas().renderComplete.disconnect(self.renderTest)

    def load_model(self):
        try:
            # Load the YOLO model
            self.model = YOLO(self.model_path)
            QMessageBox.information(None, "Model Loaded", "YOLO model loaded successfully!")
        except Exception as e:
            QMessageBox.critical(None, "Model Loading Failed", str(e))

    def run_prediction(self, raster_file, output_dir):
        if not self.model:
            QMessageBox.warning(None, "Error", "Model not loaded.")
            return

        try:
            window_size = int(3200)
            pad_size = int(600)
            window_gap = window_size - pad_size
            
            with rasterio.open(raster_file) as src:
                # Get image size
                tif_width = src.width
                tif_height = src.height
                tif_meta = src.meta.copy()

            # Calculate number of windows
            print("Prediction Start")
            num_windows_x = int(np.ceil((tif_width - pad_size) / window_gap))
            num_windows_y = int(np.ceil((tif_height - pad_size) / window_gap))
            
            fcount = 1
            totalf = len(list(product(range(num_windows_x), range(num_windows_y))))
            gdfs = []
            
            for x, y in product(range(num_windows_x), range(num_windows_y)):
                print(f"Processing image {fcount} of {totalf}")
                start_x = x * window_gap
                start_y = y * window_gap
                end_x = min(start_x + window_size, tif_width)
                end_y = min(start_y + window_size, tif_height)
                
                img_width = end_x - start_x
                img_height = end_y - start_y
                
                with rasterio.open(raster_file) as src:
                    image = src.read(window=rasterio.windows.Window(start_x, start_y, img_width, img_height))
                    img_transform = src.window_transform(rasterio.windows.Window(start_x, start_y, img_width, img_height))
                
                if image.shape[0] < image.shape[1]:
                    image = np.transpose(image, (1, 2, 0))
                
                # Padding zero for edge images that are not multiples of 32
                if (img_width != window_size) or (img_height != window_size):
                    print("Add Padding For Edge Image")
                    padding_x = (32 - img_width % 32) * (img_width % 32 > 0)
                    padding_y = (32 - img_height % 32) * (img_height % 32 > 0)
                    image = np.pad(image, ((0, padding_y), (0, padding_x), (0, 0)), 'constant', constant_values=0)
                    
                boxes = []
                confidence_scores = []
                
                # Make prediction for the image
                results = self.model.predict(image, max_det=6000, imgsz=(image.shape[0], image.shape[1]), save=False, conf=0.15)
                
                for result in results:
                    rt = result.boxes

                buildingbox=rt.cpu().data.numpy()
                    
                #remove buildings in the far side of padding area
                x_min=pad_size/2
                y_min=pad_size/2
                x_max=img_width-pad_size/2
                y_max=img_height-pad_size/2
                
                if start_x==0:
                    x_min=0
                    
                if img_width!=3200:
                    x_max=img_width
                
                if start_y==0:
                    y_min=0
                    
                if img_height!=3200:
                    y_max=img_height
                
                for resultrow in buildingbox:
                    x1, y1, x2, y2, confidence, class_id = resultrow[0],resultrow[1],resultrow[2],resultrow[3],resultrow[4],resultrow[5]     
                    
                    x_center=(x1+x2)/2
                    y_center=(y1+y2)/2
                    if (x_center<x_min)|(x_center>x_max)|(y_center<y_min)|(y_center>y_max):
                        continue
                
                    if class_id == 0:  # Assuming class_id 0 corresponds to buildings
                        boxes.append(box(
                            img_transform[2] + img_transform[0] * x1,
                            img_transform[5] + img_transform[4] * y1,
                            img_transform[2] + img_transform[0] * x2,
                            img_transform[5] + img_transform[4] * y2
                        ))
                        confidence_scores.append(confidence)
                        
                gdf = gpd.GeoDataFrame({'confidence': confidence_scores, 'geometry': boxes}).set_crs(src.crs)
                gdfs.append(gdf)
                fcount+=1
                        
            #export final prediction to shapefile
            final_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
            output_shp = os.path.join(output_dir, self.modelset+'.shp') 
            final_gdf.to_file(output_shp)
            
            vector_layer = QgsVectorLayer(output_shp, f"Prediction {os.path.basename(raster_file)}", "ogr")
            if vector_layer.isValid():
                QgsProject.instance().addMapLayer(vector_layer)
            QMessageBox.information(None, "Success", "Prediction completed and loaded into QGIS.")
        except Exception as e:
            QMessageBox.critical(None, "Prediction Failed", str(e))

    def run(self):
        dialog = YoloPredDialog()
        if dialog.exec_():
            raster_file, output_dir = dialog.getInputs()
            print("Raster file selected:", raster_file)  # Debug print
            print("Output directory selected:", output_dir)  # Debug print
            if raster_file and output_dir:
                if not self.model:
                    self.load_model()
                self.run_prediction(raster_file, output_dir)
    
    def renderTest(self, painter):
        pass
