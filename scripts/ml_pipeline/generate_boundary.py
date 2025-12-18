"""
Boundary Generation
====================
Generate Farmers_Boundary.geojson from survey point locations.

Output: GeoJSON polygon representing the geographic extent of surveyed area
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple

try:
    from shapely.geometry import Point, MultiPoint, Polygon
    from shapely.ops import unary_union
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False
    print("Warning: Shapely not installed, using simple convex hull")


class BoundaryGenerator:
    """Generate geographic boundary from survey points."""
    
    def __init__(self, data_path: str = "data/ml_prepared_data.csv"):
        self.data_path = Path(data_path)
        self.coords = None
        
    def load_coordinates(self):
        """Load survey point coordinates."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        self.coords = df[['longitude', 'latitude']].values
        print(f"✓ Loaded {len(self.coords)} survey point coordinates")
    
    def compute_convex_hull(self) -> List[List[float]]:
        """Compute convex hull of survey points."""
        
        if HAS_SHAPELY:
            # Use Shapely for robust convex hull
            points = MultiPoint([Point(lon, lat) for lon, lat in self.coords])
            hull = points.convex_hull
            
            if hull.geom_type == 'Polygon':
                coords_list = list(hull.exterior.coords)
            else:
                # Fallback if hull is a LineString or Point
                coords_list = list(hull.coords)
        else:
            # Simple convex hull using scipy
            from scipy.spatial import ConvexHull
            hull = ConvexHull(self.coords)
            coords_list = [self.coords[i].tolist() for i in hull.vertices]
            coords_list.append(coords_list[0])  # Close the polygon
        
        print(f"✓ Computed convex hull with {len(coords_list)} vertices")
        return coords_list
    
    def compute_alpha_shape(self, alpha: float = 0.05) -> List[List[float]]:
        """Compute alpha shape (tighter boundary than convex hull)."""
        
        if not HAS_SHAPELY:
            print("⚠️  Shapely not available, falling back to convex hull")
            return self.compute_convex_hull()
        
        # Create buffer around points and merge
        points = [Point(lon, lat) for lon, lat in self.coords]
        buffered = [p.buffer(alpha) for p in points]
        merged = unary_union(buffered)
        
        if merged.geom_type == 'Polygon':
            coords_list = list(merged.exterior.coords)
        elif merged.geom_type == 'MultiPolygon':
            # Use largest polygon
            largest = max(merged.geoms, key=lambda p: p.area)
            coords_list = list(largest.exterior.coords)
        else:
            # Fallback to convex hull
            return self.compute_convex_hull()
        
        print(f"✓ Computed alpha shape with {len(coords_list)} vertices (alpha={alpha})")
        return coords_list
    
    def export_geojson(
        self,
        boundary_coords: List[List[float]],
        output_file: str = "data/geojson/Farmers_Boundary.geojson",
        method: str = "convex_hull"
    ):
        """Export boundary as GeoJSON."""
        
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [boundary_coords]
                },
                "properties": {
                    "name": "Farmers Survey Boundary",
                    "method": method,
                    "n_points": len(self.coords),
                    "description": "Geographic extent of surveyed agricultural area in Mount Lebanon"
                }
            }]
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print(f"✓ Exported boundary to {output_path}")
    
    def generate_boundary(
        self,
        method: str = 'convex_hull',
        alpha: float = 0.05
    ):
        """Complete boundary generation pipeline."""
        
        print("\n=== Generating Farmers Boundary ===\n")
        
        # Load coordinates
        self.load_coordinates()
        
        # Compute boundary
        if method == 'alpha_shape':
            boundary_coords = self.compute_alpha_shape(alpha)
        else:
            boundary_coords = self.compute_convex_hull()
        
        # Export
        self.export_geojson(boundary_coords, method=method)
        
        print("\n=== Boundary Generation Complete ===")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    method = sys.argv[1] if len(sys.argv) > 1 else 'convex_hull'
    alpha = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
    
    print(f"Boundary method: {method}")
    if method == 'alpha_shape':
        print(f"Alpha parameter: {alpha}")
    
    generator = BoundaryGenerator()
    generator.generate_boundary(method=method, alpha=alpha)
