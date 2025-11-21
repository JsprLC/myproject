import geopandas as gpd
import folium
from folium import plugins
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import os
from shapely.geometry import Polygon, LineString, MultiLineString, Point
from shapely.ops import unary_union, polygonize
from collections import defaultdict

# Read the GeoJSON file - UPDATE THIS PATH
possible_paths = [
    "buildings_with_risk_data.geojson",
    "/mnt/user-data/uploads/buildings_with_risk_data.geojson",
    "../Output/Data/residential_buildings_only.geojson"
]

gdf = None
for path in possible_paths:
    if os.path.exists(path):
        print(f"Found file at: {path}")
        gdf = gpd.read_file(path)
        break

if gdf is None:
    print("ERROR: Could not find the GeoJSON file. Please update the path in the script.")
    print("Searched paths:", possible_paths)
    exit(1)

print(f"\nOriginal data loaded: {len(gdf)} features")
print(f"Geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")

# Inspect first geometry to understand structure
sample_geom = gdf.geometry.iloc[0]
print(f"\nInspecting first building geometry:")
print(f"  Type: {sample_geom.geom_type}")
if isinstance(sample_geom, MultiLineString):
    print(f"  Number of line segments: {len(sample_geom.geoms)}")
    if len(sample_geom.geoms) > 0:
        first_line = sample_geom.geoms[0]
        print(f"  First segment has {len(first_line.coords)} points")
        first_coord = list(first_line.coords)[0]
        print(f"  Coordinate example: {first_coord}")
        print(f"  Has Z coordinate: {len(first_coord) > 2}")

def extract_2d_footprint_from_3d_multilinestring(geom):
    """
    Extract 2D building footprint from 3D MultiLineString.
    
    The MultiLineString contains individual edge segments of a 3D building.
    Each segment is a separate LineString (usually just 2 points - start and end).
    We need to:
    1. Collect all unique points at ground level
    2. Find which segments connect to form the ground footprint
    3. Create a polygon from those segments
    """
    if geom is None or geom.is_empty:
        return None
    
    try:
        if not isinstance(geom, MultiLineString):
            return None
        
        # Collect all points with their Z values
        all_points_3d = []
        all_segments_2d = []
        
        for line in geom.geoms:
            coords = list(line.coords)
            # Each segment typically has 2 points (start, end)
            for coord in coords:
                if len(coord) >= 3:
                    all_points_3d.append(coord)
                    
        if not all_points_3d:
            return None
        
        # Find the minimum Z (ground level)
        z_values = [p[2] for p in all_points_3d]
        min_z = min(z_values)
        tolerance = 0.5  # Allow small floating point differences
        
        print(f"    Z range: {min_z:.2f} to {max(z_values):.2f}, using ground level: {min_z:.2f}")
        
        # Collect all 2D segments at ground level
        ground_segments = []
        for line in geom.geoms:
            coords = list(line.coords)
            if len(coords) >= 2:
                # Check if both endpoints are at ground level
                p1 = coords[0]
                p2 = coords[-1]
                
                if len(p1) >= 3 and len(p2) >= 3:
                    z1, z2 = p1[2], p2[2]
                    
                    # If both points are at ground level, this is a ground edge
                    if abs(z1 - min_z) < tolerance and abs(z2 - min_z) < tolerance:
                        # Create 2D line segment
                        seg_2d = LineString([(p1[0], p1[1]), (p2[0], p2[1])])
                        if seg_2d.length > 1e-10:  # Ignore zero-length segments
                            ground_segments.append(seg_2d)
        
        print(f"    Found {len(ground_segments)} ground-level segments")
        
        if not ground_segments:
            print(f"    ⚠️  No ground segments found, trying alternative method...")
            # Alternative: get all unique 2D points at ground level
            ground_points = set()
            for p in all_points_3d:
                if abs(p[2] - min_z) < tolerance:
                    ground_points.add((p[0], p[1]))
            
            if len(ground_points) >= 3:
                # Create convex hull of ground points
                from shapely.geometry import MultiPoint
                mp = MultiPoint(list(ground_points))
                polygon = mp.convex_hull
                print(f"    Created convex hull from {len(ground_points)} ground points")
                return polygon if polygon.is_valid else None
            return None
        
        # Try to create polygon from ground segments
        try:
            # Method 1: Use polygonize to form polygons from line segments
            polygons = list(polygonize(ground_segments))
            
            if polygons:
                if len(polygons) == 1:
                    polygon = polygons[0]
                else:
                    # Multiple polygons, take the largest one (main building footprint)
                    polygon = max(polygons, key=lambda p: p.area)
                
                print(f"    ✓ Created polygon with {len(polygon.exterior.coords)} vertices")
                
                # Validate
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                
                if polygon.is_valid and not polygon.is_empty and polygon.area > 1e-10:
                    return polygon
        
        except Exception as e:
            print(f"    Polygonize failed: {e}")
        
        # Method 2: Collect unique points and create convex hull
        print(f"    Trying convex hull method...")
        unique_2d_points = set()
        for seg in ground_segments:
            for coord in seg.coords:
                unique_2d_points.add((coord[0], coord[1]))
        
        if len(unique_2d_points) >= 3:
            from shapely.geometry import MultiPoint
            mp = MultiPoint(list(unique_2d_points))
            polygon = mp.convex_hull
            
            if polygon.geom_type == 'Polygon' and polygon.is_valid and not polygon.is_empty:
                print(f"    ✓ Created convex hull polygon")
                return polygon
        
        print(f"    ✗ Could not create valid polygon")
        return None
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None

print("\n" + "="*60)
print("EXTRACTING 2D FOOTPRINTS FROM 3D BUILDING GEOMETRIES")
print("="*60)

# Apply conversion with progress
converted_geometries = []
for idx, geom in enumerate(gdf.geometry):
    if idx < 5 or idx % 20 == 0:  # Print progress for first 5 and every 20th
        print(f"\n  Building {idx + 1}/{len(gdf)}:")
    
    footprint = extract_2d_footprint_from_3d_multilinestring(geom)
    converted_geometries.append(footprint)

gdf['geometry'] = converted_geometries

# Remove any None geometries
initial_count = len(gdf)
gdf = gdf[gdf['geometry'].notna()].copy()
final_count = len(gdf)

print(f"\n" + "="*60)
print(f"Buildings processed: {initial_count}")
print(f"Valid footprints created: {final_count}")
if final_count < initial_count:
    print(f"⚠️  Warning: {initial_count - final_count} buildings could not be converted")

if len(gdf) > 0:
    print(f"New geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")
    
    # Check if all are now Polygons
    if all(gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])):
        print("\n✅ SUCCESS: All geometries are now 2D Polygons!")
    else:
        print("\n⚠️  Warning: Some geometries may not be Polygons")
else:
    print("\n❌ ERROR: No valid geometries after conversion!")
    exit(1)

# Convert to WGS84 if needed
if gdf.crs and gdf.crs != "EPSG:4326":
    print(f"Converting from {gdf.crs} to EPSG:4326...")
    gdf = gdf.to_crs("EPSG:4326")

# Calculate risk metrics
gdf['risk_percentile'] = gdf['expected_deaths_mean'].rank(pct=True) * 100
gdf['cv'] = gdf['expected_deaths_std'] / (gdf['expected_deaths_mean'] + 1e-10)

# Assign risk categories
def assign_risk_category(percentile):
    if percentile >= 95:
        return "Very High (Top 5%)", "#8B0000"
    elif percentile >= 90:
        return "High (90-95%)", "#DC143C"
    elif percentile >= 75:
        return "Elevated (75-90%)", "#FF8C00"
    elif percentile >= 50:
        return "Moderate (50-75%)", "#FFD700"
    elif percentile >= 25:
        return "Low-Moderate (25-50%)", "#9ACD32"
    else:
        return "Low (Bottom 25%)", "#228B22"

gdf[['risk_category', 'category_color']] = gdf['risk_percentile'].apply(
    lambda x: pd.Series(assign_risk_category(x))
)

# Create map
center_lat = gdf.geometry.centroid.y.mean()
center_lon = gdf.geometry.centroid.x.mean()

print("\n" + "="*60)
print("CREATING INTERACTIVE MAP")
print("="*60)

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=17,
    tiles='CartoDB positron'
)

folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)

# Add buildings
for idx, row in gdf.iterrows():
    popup_html = f"""
    <div style="width: 320px; font-family: Arial, sans-serif;">
        <h3 style="margin: 0 0 10px 0; padding: 8px; background-color: {row['category_color']}; 
                   color: white; text-align: center;">
            {row['risk_category']}
        </h3>
        <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
            <tr style="background-color: #f0f0f0;">
                <td colspan="2" style="padding: 5px; font-weight: bold;">Risk Metrics</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Expected Deaths (Mean):</b></td>
                <td style="text-align: right; padding: 5px;">{row['expected_deaths_mean']:.4e}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Expected Deaths (Std):</b></td>
                <td style="text-align: right; padding: 5px;">{row['expected_deaths_std']:.4e}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Coefficient of Variation:</b></td>
                <td style="text-align: right; padding: 5px;">{row['cv']:.3f}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Risk Percentile:</b></td>
                <td style="text-align: right; padding: 5px; font-weight: bold; color: {row['category_color']};">
                    {row['risk_percentile']:.1f}%
                </td>
            </tr>
            <tr style="background-color: #f0f0f0;">
                <td colspan="2" style="padding: 5px; font-weight: bold;">Building Information</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Occupants:</b></td>
                <td style="text-align: right; padding: 5px;">{row['num_occupants']:.0f}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Height:</b></td>
                <td style="text-align: right; padding: 5px;">{row['citygml_measured_height']:.2f} {row['citygml_measured_height_units']}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Storeys:</b></td>
                <td style="text-align: right; padding: 5px;">{row['citygml_storeys_above_ground']}</td>
            </tr>
        </table>
    </div>
    """
    
    geojson = folium.GeoJson(
        data=row['geometry'].__geo_interface__,
        style_function=lambda x, color=row['category_color']: {
            'fillColor': color,
            'color': color,
            'weight': 1,
            'fillOpacity': 0.85,
            'opacity': 1.0
        },
        highlight_function=lambda x, color=row['category_color']: {
            'fillColor': color,
            'color': 'white',
            'weight': 2.5,
            'fillOpacity': 1.0
        },
        tooltip=folium.Tooltip(
            f"<b>{row['risk_category']}</b><br>Risk: {row['expected_deaths_mean']:.3e}",
            sticky=False
        ),
        popup=folium.Popup(popup_html, max_width=350)
    )
    geojson.add_to(m)

# Statistics
vmin = gdf['expected_deaths_mean'].min()
vmax = gdf['expected_deaths_mean'].max()
median = gdf['expected_deaths_mean'].median()

# Add legend
legend_html = f'''
<div style="position: fixed; bottom: 50px; right: 50px; width: 280px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:13px; padding: 15px; box-shadow: 3px 3px 10px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 15px; 
              border-bottom: 2px solid #333; padding-bottom: 5px;">
        Building Risk Classification
    </p>
    <div style="margin: 8px 0;">
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #8B0000; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px;"></span>
            <span style="font-size: 12px;"><b>Very High</b> (Top 5%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #DC143C; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px;"></span>
            <span style="font-size: 12px;"><b>High</b> (90-95%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #FF8C00; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px;"></span>
            <span style="font-size: 12px;"><b>Elevated</b> (75-90%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #FFD700; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px;"></span>
            <span style="font-size: 12px;"><b>Moderate</b> (50-75%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #9ACD32; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px;"></span>
            <span style="font-size: 12px;"><b>Low-Moderate</b> (25-50%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #228B22; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px;"></span>
            <span style="font-size: 12px;"><b>Low</b> (Bottom 25%)</span>
        </div>
    </div>
    <p style="margin-top: 12px; font-size: 11px; border-top: 1px solid #ddd; 
              padding-top: 8px; background-color: #f9f9f9; padding: 8px;">
        Min: {vmin:.3e}<br>
        Median: {median:.3e}<br>
        Max: {vmax:.3e}
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl().add_to(m)
plugins.Fullscreen().add_to(m)
plugins.MeasureControl(position='topleft', primary_length_unit='meters').add_to(m)

# Save
output_path = "../Output/Maps/building_risk_FINAL.html"
m.save(output_path)

print(f"\n{'='*60}")
print(f"✅ SUCCESS: SOLID BUILDING FOOTPRINTS CREATED!")
print(f"{'='*60}")
print(f"Map saved to: {output_path}")
print(f"Buildings: {len(gdf)}")
print(f"Risk range: {vmin:.4e} to {vmax:.4e}")

# Save converted data
output_geojson = "../Output/Data/buildings_with_risk_2D_FINAL.geojson"
gdf.to_file(output_geojson, driver='GeoJSON')
print(f"\n✅ 2D footprint data saved to: {output_geojson}")

# Print category stats
print(f"\n{'='*60}")
print("RISK CATEGORY DISTRIBUTION")
print(f"{'='*60}")
for name, low, high in [
    ("Very High (Top 5%)", 95, 100),
    ("High (90-95%)", 90, 95),
    ("Elevated (75-90%)", 75, 90),
    ("Moderate (50-75%)", 50, 75),
    ("Low-Moderate (25-50%)", 25, 50),
    ("Low (Bottom 25%)", 0, 25)
]:
    subset = gdf[(gdf['risk_percentile'] >= low) & (gdf['risk_percentile'] < high)]
    print(f"{name}: {len(subset)} buildings ({len(subset)/len(gdf)*100:.1f}%)")
