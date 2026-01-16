"""Google Earth Engine integration for AlphaEarth similarity search."""

ee = None


class GEESimilaritySearch:
    """Similarity search engine using GEE AlphaEarth embeddings."""
    
    def __init__(self):
        self._initialized = False
    
    def _ensure_initialized(self):
        """Initialize GEE with lazy import."""
        global ee
        
        if ee is None:
            try:
                import ee as _ee
                ee = _ee
            except ImportError:
                raise RuntimeError(
                    "Google Earth Engine plugin is required. "
                    "Please install from QGIS Plugin Manager and connect your Google Cloud Project."
                )
        
        if not self._initialized:
            try:
                ee.Initialize()
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Unable to initialize Google Earth Engine: {e}")
    
    def run_similarity_search_geometry(self, geom_type, geom_data, buffer_km=5, 
                                        year_start=2023, year_end=None, max_threshold=0.5):
        """Run similarity search for any geometry type.
        
        Returns dict with: similarity_image, search_area, reference_geom, vis_params, geom_type
        """
        self._ensure_initialized()
        
        if year_end is None:
            year_end = year_start
        
        if geom_type == 'point':
            reference_geom = ee.Geometry.Point([geom_data['lon'], geom_data['lat']])
            # Use square bounding box instead of circular buffer
            buffer_degrees = buffer_km / 111.0  # Approximate km to degrees
            search_area = ee.Geometry.Rectangle([
                geom_data['lon'] - buffer_degrees,
                geom_data['lat'] - buffer_degrees,
                geom_data['lon'] + buffer_degrees,
                geom_data['lat'] + buffer_degrees
            ])
        elif geom_type == 'bbox':
            reference_geom = ee.Geometry.Rectangle([
                geom_data['min_lon'], geom_data['min_lat'],
                geom_data['max_lon'], geom_data['max_lat']
            ])
            search_area = reference_geom
        elif geom_type == 'polygon':
            reference_geom = ee.Geometry.Polygon([geom_data['coords']])
            search_area = reference_geom
        else:
            raise ValueError(f"Unknown geometry type: {geom_type}")
        
        start_date = f"{year_start}-01-01"
        end_date = f"{year_end + 1}-01-01"
        
        embeddings = ee.ImageCollection('GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL') \
            .filterDate(start_date, end_date) \
            .filterBounds(search_area)
        
        # Check if we have any embeddings
        if embeddings.size().getInfo() == 0:
            raise RuntimeError(
                f"No AlphaEarth embeddings found for this location and year ({year_start}). "
                f"AlphaEarth coverage may be limited. Try a different location or year (2017-2023)."
            )
        
        embeddings_image = embeddings.mosaic()
        
        target_vector = embeddings_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=reference_geom,
            scale=30,  # Optimized: 30m instead of 10m (9x fewer pixels)
            maxPixels=1e9,
            bestEffort=True  # Allow GEE to use approximations for speed
        )
        
        # Verify we got embedding values
        band_names = embeddings_image.bandNames().getInfo()
        if not band_names or len(band_names) == 0:
            raise RuntimeError(
                "No embedding bands found. The reference location may be outside AlphaEarth coverage."
            )
        
        target_image = target_vector.toImage(band_names)
        
        diff = embeddings_image.subtract(target_image)
        squared_diff = diff.pow(2)
        sum_squared_diff = squared_diff.reduce(ee.Reducer.sum())
        euclidean_distance = sum_squared_diff.sqrt()
        
        similarity_image = euclidean_distance.clip(search_area)
        
        vis_params = {
            'min': 0,
            'max': max_threshold,
            'palette': ['#00FF00', '#FFFF00', '#FF0000']
        }
        
        return {
            'similarity_image': similarity_image,
            'search_area': search_area,
            'reference_geom': reference_geom,
            'vis_params': vis_params,
            'geom_type': geom_type,
        }
    
    def run_similarity_search(self, lon, lat, buffer_km=5, year=2023, max_threshold=0.5, shape="circle"):
        """Legacy method for backward compatibility."""
        if shape == "square":
            half_side_deg = buffer_km / 111.0
            geom_data = {
                'min_lon': lon - half_side_deg,
                'min_lat': lat - half_side_deg,
                'max_lon': lon + half_side_deg,
                'max_lat': lat + half_side_deg
            }
            result = self.run_similarity_search_geometry('bbox', geom_data, buffer_km, year, max_threshold)
        else:
            geom_data = {'lon': lon, 'lat': lat}
            result = self.run_similarity_search_geometry('point', geom_data, buffer_km, year, max_threshold)
        
        result['point_source'] = result['reference_geom']
        result['shape'] = shape
        result['buffer_km'] = buffer_km
        return result


def export_gee_image_to_file(ee_image, geometry, file_path, scale, vis_params, color_palette, export_format='geotiff'):
    """Export GEE image to local file.
    
    Args:
        ee_image: ee.Image to export
        geometry: ee.Geometry defining the export region
        file_path: Local file path to save to
        scale: Resolution in meters
        vis_params: Visualization parameters dict
        color_palette: List of color hex codes
        export_format: 'geotiff', 'cog', or 'png'
    """
    global ee
    if ee is None:
        import ee as _ee
        ee = _ee
    
    # Apply visualization with colors for export
    vis_params_copy = vis_params.copy()
    if color_palette:
        vis_params_copy['palette'] = color_palette
    
    # Always visualize to preserve colors in export
    image_to_export = ee_image.visualize(**vis_params_copy)
    file_format = 'GeoTIFF'
    
    # Clip to geometry and get download URL
    try:
        url = image_to_export.clip(geometry).getDownloadURL({
            'scale': scale,
            'crs': 'EPSG:4326',
            'fileFormat': file_format,
            'region': geometry.getInfo()['coordinates'] if geometry.type().getInfo() == 'Polygon' else geometry.bounds().getInfo()['coordinates']
        })
        
        # Download file
        import requests
        import time
        
        print(f"Downloading from GEE... (scale={scale}m)")
        start_time = time.time()
        
        response = requests.get(url, timeout=120)  # 2 minute timeout
        response.raise_for_status()
        
        # GEE often returns ZIP files, so we need to handle that
        content_type = response.headers.get('Content-Type', '')
        is_zip = 'zip' in content_type or response.content.startswith(b'PK')
        
        elapsed = time.time() - start_time
        file_size_mb = len(response.content) / (1024 * 1024)
        print(f"Downloaded {file_size_mb:.2f} MB in {elapsed:.1f} seconds")
        
        if is_zip:
            print("Response is a ZIP file, extracting...")
            import zipfile
            import io
            import tempfile
            import os
            
            # Extract ZIP content
            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer) as zip_file:
                # Find the first .tif or .png file in the ZIP
                target_ext = '.tif' if export_format in ['geotiff', 'cog'] else '.png'
                tif_files = [name for name in zip_file.namelist() if name.endswith(target_ext)]
                
                if not tif_files:
                    raise RuntimeError(f"No {target_ext} file found in downloaded ZIP")
                
                # Extract to a temporary location first
                temp_dir = tempfile.mkdtemp()
                extracted_file = zip_file.extract(tif_files[0], temp_dir)
                
                # Read the extracted file and write to final destination
                with open(extracted_file, 'rb') as src:
                    with open(file_path, 'wb') as dst:
                        dst.write(src.read())
                
                # Clean up temp directory
                import shutil
                shutil.rmtree(temp_dir)
                
            print(f"Extracted {target_ext} file from ZIP to {file_path}")
        else:
            # Direct file, write as-is
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved file directly to {file_path}")
        
        # For COG format, convert using GDAL
        if export_format == 'cog':
            _convert_to_cog(file_path)
        
        # For PNG, create world file
        if export_format == 'png':
            _create_world_file(file_path, geometry)
        
        return file_path
        
    except Exception as e:
        raise RuntimeError(f"GEE export failed: {str(e)}")


def _convert_to_cog(file_path):
    """Convert GeoTIFF to Cloud Optimized GeoTIFF."""
    try:
        from osgeo import gdal
        import tempfile
        import os
        
        # Create temp file
        temp_path = file_path.replace('.tif', '_temp.tif')
        os.rename(file_path, temp_path)
        
        # Convert to COG
        gdal.Translate(
            file_path,
            temp_path,
            creationOptions=['TILED=YES', 'COMPRESS=LZW', 'COPY_SRC_OVERVIEWS=YES']
        )
        
        # Clean up
        os.remove(temp_path)
        print("Converted to Cloud Optimized GeoTIFF")
        
    except Exception as e:
        print(f"COG conversion failed, keeping as regular GeoTIFF: {e}")
        # If conversion fails, just rename temp back
        if os.path.exists(temp_path):
            os.rename(temp_path, file_path)


def _create_world_file(png_path, geometry):
    """Create world file (.pgw) for PNG."""
    try:
        bounds = geometry.bounds().getInfo()['coordinates'][0]
        min_x = min(p[0] for p in bounds)
        max_x = max(p[0] for p in bounds)
        min_y = min(p[1] for p in bounds)
        max_y = max(p[1] for p in bounds)
        
        # Assume standard 512x512 image from GEE
        width = 512
        height = 512
        
        pixel_size_x = (max_x - min_x) / width
        pixel_size_y = (max_y - min_y) / height
        
        world_file = png_path.replace('.png', '.pgw')
        with open(world_file, 'w') as f:
            f.write(f"{pixel_size_x}\n")     # Pixel size X
            f.write("0.0\n")                 # Rotation X
            f.write("0.0\n")                 # Rotation Y  
            f.write(f"-{pixel_size_y}\n")   # Pixel size Y (negative)
            f.write(f"{min_x}\n")            # Upper left X
            f.write(f"{max_y}\n")            # Upper left Y
        
        print(f"Created world file: {world_file}")
        
    except Exception as e:
        print(f"World file creation failed: {e}")
