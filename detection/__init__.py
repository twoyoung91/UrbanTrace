# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 20:19:57 2024

@author: Yang Yang
"""
from ultralytics import YOLO

class detection(input_raster, model_path, output_dir):
    def __init__(self, modeltype):
        if modeltype == "detection"：
            self.model_path = os.path.join(self.plugin_dir,"detection.pt") 
            self.modelset = "detection"
        elif modeltype == "segmentation":
            self.model_path = os.path.join(self.plugin_dir,"segmentation.pt") 
            self.modelset = "segmentation"
        else:
            raise ValueError("Invalid model type specified. Use 'detection' or 'segmentation'.")
        self.model = None

    def run_detection(self, input_raster, model_path, output_dir):
        """
        Run detection on the input raster using the YOLO model.
        
        Parameters:
        - input_raster: Path to the input raster file.
        - model_path: Path to the YOLO model file.
        - output_dir: Directory to save the output vector layer.
        
        Returns:
        - None
        """
        try:
            # Load the YOLO model
            model = YOLO(model_path)
            
            # Perform detection
            results = model.predict(source=input_raster, save=True, save_txt=True)
            
            # Process results and save to vector layer
            # (Implementation details would go here)
            
            print("Detection completed successfully.")
            
        except Exception as e:
            print(f"Error during detection: {e}")