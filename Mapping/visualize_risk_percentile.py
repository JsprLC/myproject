import geopandas as gpd
import folium
from folium import plugins
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import os

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

# Convert to WGS84 (EPSG:4326) for web mapping if not already
if gdf.crs != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")

# Calculate percentile ranks for better visualization of small values
gdf['risk_percentile'] = gdf['expected_deaths_mean'].rank(pct=True) * 100

# Get the center of the map
center_lat = gdf.geometry.centroid.y.mean()
center_lon = gdf.geometry.centroid.x.mean()

# Create a base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
    tiles='CartoDB positron'
)

# Add alternative tile layers
folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)

# Use percentile-based coloring for better discrimination
colormap = plt.cm.get_cmap('RdYlGn_r')  # Red for high risk, green for low

def get_color_from_percentile(percentile):
    """Convert percentile (0-100) to color"""
    if pd.isna(percentile):
        return '#808080'  # Gray for missing values
    
    normalized = percentile / 100.0
    rgba = colormap(normalized)
    return mcolors.rgb2hex(rgba)

# Statistics
vmin = gdf['expected_deaths_mean'].min()
vmax = gdf['expected_deaths_mean'].max()
median = gdf['expected_deaths_mean'].median()
p25 = gdf['expected_deaths_mean'].quantile(0.25)
p75 = gdf['expected_deaths_mean'].quantile(0.75)
p90 = gdf['expected_deaths_mean'].quantile(0.90)
p95 = gdf['expected_deaths_mean'].quantile(0.95)

print("\n" + "="*60)
print("RISK VALUE DISTRIBUTION")
print("="*60)
print(f"Buildings: {len(gdf)}")
print(f"\nAbsolute values (scientific notation):")
print(f"  Minimum:  {vmin:.4e}")
print(f"  25th pct: {p25:.4e}")
print(f"  Median:   {median:.4e}")
print(f"  75th pct: {p75:.4e}")
print(f"  90th pct: {p90:.4e}")
print(f"  95th pct: {p95:.4e}")
print(f"  Maximum:  {vmax:.4e}")

# Add buildings to the map with percentile-based coloring
for idx, row in gdf.iterrows():
    # Get color based on percentile
    color = get_color_from_percentile(row['risk_percentile'])
    
    # Calculate coefficient of variation
    cv = row['expected_deaths_std'] / row['expected_deaths_mean'] if row['expected_deaths_mean'] > 0 else np.nan
    
    # Determine risk category based on percentiles
    if row['risk_percentile'] >= 95:
        risk_category = "Very High (Top 5%)"
        category_color = "#8B0000"
    elif row['risk_percentile'] >= 90:
        risk_category = "High (Top 10%)"
        category_color = "#DC143C"
    elif row['risk_percentile'] >= 75:
        risk_category = "Elevated (Top 25%)"
        category_color = "#FF8C00"
    elif row['risk_percentile'] >= 50:
        risk_category = "Moderate"
        category_color = "#FFD700"
    elif row['risk_percentile'] >= 25:
        risk_category = "Low-Moderate"
        category_color = "#9ACD32"
    else:
        risk_category = "Low (Bottom 25%)"
        category_color = "#228B22"
    
    # Create enhanced popup with risk information
    popup_html = f"""
    <div style="width: 320px; font-family: Arial, sans-serif;">
        <h3 style="margin: 0 0 10px 0; padding: 8px; background-color: {category_color}; 
                   color: white; text-align: center;">
            {risk_category}
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
                <td style="text-align: right; padding: 5px;">{cv:.3f}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Risk Percentile:</b></td>
                <td style="text-align: right; padding: 5px; font-weight: bold; color: {category_color};">
                    {row['risk_percentile']:.1f}%
                </td>
            </tr>
            <tr style="background-color: #f0f0f0;">
                <td colspan="2" style="padding: 5px; font-weight: bold;">Building Information</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Number of Occupants:</b></td>
                <td style="text-align: right; padding: 5px;">{row['num_occupants']:.0f}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Building Height:</b></td>
                <td style="text-align: right; padding: 5px;">{row['citygml_measured_height']:.2f} {row['citygml_measured_height_units']}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Storeys:</b></td>
                <td style="text-align: right; padding: 5px;">{row['citygml_storeys_above_ground']}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>Roof Type:</b></td>
                <td style="text-align: right; padding: 5px;">{row['citygml_roof_type']}</td>
            </tr>
        </table>
    </div>
    """
    
    # Add the building polygon as a filled block
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': color,  # Border color same as fill for solid block appearance
            'weight': 0.5,   # Thin border
            'fillOpacity': 0.85,  # More opaque for solid block appearance
            'opacity': 1.0   # Solid border
        },
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=f"Percentile: {row['risk_percentile']:.1f}% | Risk: {row['expected_deaths_mean']:.3e}"
    ).add_to(m)

# Add enhanced legend with percentile information
legend_html = f'''
<div style="position: fixed; 
            bottom: 50px; right: 50px; width: 280px; height: auto; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:13px; padding: 15px; box-shadow: 3px 3px 10px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 15px; 
              border-bottom: 2px solid #333; padding-bottom: 5px;">
        Risk Classification (Percentile-Based)
    </p>
    
    <div style="margin: 8px 0;">
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #8B0000; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px; border: 1px solid black;"></span>
            <span style="font-size: 12px;"><b>Very High</b> (Top 5%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #DC143C; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px; border: 1px solid black;"></span>
            <span style="font-size: 12px;"><b>High</b> (90-95%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #FF8C00; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px; border: 1px solid black;"></span>
            <span style="font-size: 12px;"><b>Elevated</b> (75-90%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #FFD700; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px; border: 1px solid black;"></span>
            <span style="font-size: 12px;"><b>Moderate</b> (50-75%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #9ACD32; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px; border: 1px solid black;"></span>
            <span style="font-size: 12px;"><b>Low-Moderate</b> (25-50%)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background-color: #228B22; width: 25px; height: 15px; 
                         display: inline-block; margin-right: 8px; border: 1px solid black;"></span>
            <span style="font-size: 12px;"><b>Low</b> (Bottom 25%)</span>
        </div>
    </div>
    
    <p style="margin-top: 12px; font-size: 11px; border-top: 1px solid #ddd; 
              padding-top: 8px; background-color: #f9f9f9; padding: 8px; border-radius: 4px;">
        <b>Absolute Values:</b><br>
        Min: {vmin:.3e}<br>
        Median: {median:.3e}<br>
        95th %ile: {p95:.3e}<br>
        Max: {vmax:.3e}
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add layer control
folium.LayerControl().add_to(m)

# Add fullscreen option
plugins.Fullscreen().add_to(m)

# Add measurement tool
plugins.MeasureControl(position='topleft', primary_length_unit='meters').add_to(m)

# Save the map
output_path = "../Output/Maps/building_risk_percentile_map.html"
m.save(output_path)

print(f"\n{'='*60}")
print(f"INTERACTIVE MAP GENERATED")
print(f"{'='*60}")
print(f"Map saved to: {output_path}")
print(f"\nKey Features:")
print("  - Percentile-based coloring for better discrimination")
print("  - 6 risk categories (Very High, High, Elevated, Moderate, Low-Moderate, Low)")
print("  - Detailed popups with risk metrics and building info")
print("  - Multiple base map layers")
print("  - Measurement tool for distance/area")
print("  - Fullscreen mode")

# Print category distribution
print(f"\n{'='*60}")
print("RISK CATEGORY DISTRIBUTION")
print(f"{'='*60}")
categories = [
    ("Very High (Top 5%)", 95, 100),
    ("High (90-95%)", 90, 95),
    ("Elevated (75-90%)", 75, 90),
    ("Moderate (50-75%)", 50, 75),
    ("Low-Moderate (25-50%)", 25, 50),
    ("Low (Bottom 25%)", 0, 25)
]

for name, low, high in categories:
    count = len(gdf[(gdf['risk_percentile'] >= low) & (gdf['risk_percentile'] < high)])
    total_risk = gdf[(gdf['risk_percentile'] >= low) & (gdf['risk_percentile'] < high)]['expected_deaths_mean'].sum()
    total_occupants = gdf[(gdf['risk_percentile'] >= low) & (gdf['risk_percentile'] < high)]['num_occupants'].sum()
    print(f"\n{name}:")
    print(f"  Buildings: {count} ({count/len(gdf)*100:.1f}%)")
    print(f"  Total expected deaths: {total_risk:.4e}")
    print(f"  Total occupants: {total_occupants:.0f}")
