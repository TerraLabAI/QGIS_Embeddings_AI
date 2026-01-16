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
            search_area = reference_geom.buffer(buffer_km * 1000)
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
        
        embeddings_image = embeddings.mosaic()
        
        target_vector = embeddings_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=reference_geom,
            scale=10,
            maxPixels=1e9
        )
        
        target_image = target_vector.toImage(embeddings_image.bandNames())
        
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
