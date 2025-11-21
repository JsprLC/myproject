import geopandas as gpd
import folium
from folium import plugins
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Read the GeoJSON file - adjust this path as needed
# Try multiple possible paths
import os
import pandas as pd

possible_paths = [
    "buildings_with_risk_data.geojson",
    "/mnt/user-data/uploads/buildings_with_risk_data.geojson",
    "../Output/residential_buildings_only.geojson"
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

# Get the center of the map
center_lat = gdf.geometry.centroid.y.mean()
center_lon = gdf.geometry.centroid.x.mean()

# Create a base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
    tiles='OpenStreetMap'
)

# Add alternative tile layers
folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(m)
folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)

# Create a colormap for expected deaths mean
vmin = gdf['expected_deaths_mean'].min()
vmax = gdf['expected_deaths_mean'].max()

# For very small values, use log scale if range spans multiple orders of magnitude
value_range = vmax / vmin if vmin > 0 else 1
use_log_scale = value_range > 10

if use_log_scale:
    print(f"Using log scale for visualization (range: {value_range:.1f}x)")
    # Add small epsilon to avoid log(0)
    gdf['log_risk'] = np.log10(gdf['expected_deaths_mean'] + 1e-10)
    vmin_plot = gdf['log_risk'].min()
    vmax_plot = gdf['log_risk'].max()
else:
    print(f"Using linear scale for visualization")
    vmin_plot = vmin
    vmax_plot = vmax

# Create a colormap (red for high risk, yellow for medium, green for low)
colormap = plt.cm.get_cmap('YlOrRd')

def get_color(value, vmin, vmax, use_log=False):
    """Convert value to color using colormap"""
    if pd.isna(value):
        return '#808080'  # Gray for missing values
    
    if use_log:
        # Use log scale
        value_transformed = np.log10(value + 1e-10)
    else:
        value_transformed = value
    
    normalized = (value_transformed - vmin) / (vmax - vmin) if vmax > vmin else 0
    normalized = np.clip(normalized, 0, 1)  # Ensure in [0, 1]
    rgba = colormap(normalized)
    return mcolors.rgb2hex(rgba)

# Add buildings to the map
for idx, row in gdf.iterrows():
    # Get color based on expected deaths mean
    color = get_color(row['expected_deaths_mean'], vmin_plot, vmax_plot, use_log_scale)
    
    # Create popup with risk information (using scientific notation for small values)
    popup_html = f"""
    <div style="width: 280px;">
        <h4 style="margin-bottom: 10px;">Building Risk Information</h4>
        <table style="width: 100%; font-size: 12px;">
            <tr>
                <td><b>Expected Deaths (Mean):</b></td>
                <td style="text-align: right;">{row['expected_deaths_mean']:.4e}</td>
            </tr>
            <tr>
                <td><b>Expected Deaths (Std):</b></td>
                <td style="text-align: right;">{row['expected_deaths_std']:.4e}</td>
            </tr>
            <tr>
                <td><b>Coefficient of Variation:</b></td>
                <td style="text-align: right;">{row['expected_deaths_std']/row['expected_deaths_mean']:.3f}</td>
            </tr>
            <tr style="border-top: 1px solid #ccc;">
                <td><b>Number of Occupants:</b></td>
                <td style="text-align: right;">{row['num_occupants']:.0f}</td>
            </tr>
            <tr>
                <td><b>Building Height:</b></td>
                <td style="text-align: right;">{row['citygml_measured_height']:.2f} {row['citygml_measured_height_units']}</td>
            </tr>
            <tr>
                <td><b>Storeys:</b></td>
                <td style="text-align: right;">{row['citygml_storeys_above_ground']}</td>
            </tr>
            <tr>
                <td><b>Roof Type:</b></td>
                <td style="text-align: right;">{row['citygml_roof_type']}</td>
            </tr>
        </table>
    </div>
    """
    
    # Add the building polygon as a filled block
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': color,  # Border color matches fill for solid appearance
            'weight': 0.5,
            'fillOpacity': 0.85,
            'opacity': 1.0
        },
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Risk: {row['expected_deaths_mean']:.3e}"
    ).add_to(m)

# Add a custom legend with scientific notation
scale_text = " (Log Scale)" if use_log_scale else ""
legend_html = f'''
<div style="position: fixed; 
            bottom: 50px; right: 50px; width: 220px; height: auto; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:13px; padding: 12px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin-bottom: 8px; font-weight: bold; font-size: 14px;">Expected Deaths (Mean){scale_text}</p>
    <div style="margin: 5px 0;">
        <span style="background: linear-gradient(to right, #FFFFCC, #FEB24C, #F03B20); 
                     display: block; height: 15px; border: 1px solid #999;"></span>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 3px;">
        <span>Low</span>
        <span>High</span>
    </div>
    <p style="margin-top: 10px; font-size: 11px; border-top: 1px solid #ddd; padding-top: 8px;">
        <b>Range:</b><br>
        Min: {vmin:.3e}<br>
        Max: {vmax:.3e}<br>
        Median: {gdf['expected_deaths_mean'].median():.3e}
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add layer control
folium.LayerControl().add_to(m)

# Add fullscreen option
plugins.Fullscreen().add_to(m)

# Save the map
output_path = "../Output/building_risk_map.html"
m.save(output_path)

print(f"Map created successfully!")
print(f"Number of buildings: {len(gdf)}")
print(f"Expected deaths range: {vmin:.4e} - {vmax:.4e}")
print(f"Scale type: {'Logarithmic' if use_log_scale else 'Linear'}")
print(f"Map saved to: {output_path}")

# Also create a statistical summary
print("\n=== Risk Statistics ===")
print(f"Mean expected deaths: {gdf['expected_deaths_mean'].mean():.4e}")
print(f"Median expected deaths: {gdf['expected_deaths_mean'].median():.4e}")
print(f"Total expected deaths: {gdf['expected_deaths_mean'].sum():.4e}")
print(f"Total occupants: {gdf['num_occupants'].sum():.0f}")

# Show top 5 highest risk buildings
print("\n=== Top 5 Highest Risk Buildings ===")
top_5 = gdf.nlargest(5, 'expected_deaths_mean')[['expected_deaths_mean', 'expected_deaths_std', 'num_occupants']]
for idx, (i, row) in enumerate(top_5.iterrows(), 1):
    print(f"{idx}. Mean: {row['expected_deaths_mean']:.4e}, Std: {row['expected_deaths_std']:.4e}, Occupants: {row['num_occupants']:.0f}")
