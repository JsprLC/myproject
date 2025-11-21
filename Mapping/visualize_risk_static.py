import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import numpy as np
import os

# Read the GeoJSON file - UPDATE THIS PATH
file_path = "../Output/Data/buildings_with_risk_2D_FINAL.geojson"  # Change this to your file path

if not os.path.exists(file_path):
    print(f"ERROR: File not found at {file_path}")
    print("Please update the 'file_path' variable in the script.")
    exit(1)

gdf = gpd.read_file(file_path)

print(f"Loaded {len(gdf)} buildings")
print(f"Columns: {list(gdf.columns)}")

# Check if values are very small and need special handling
vmin = gdf['expected_deaths_mean'].min()
vmax = gdf['expected_deaths_mean'].max()
value_range = vmax / vmin if vmin > 0 else 1
use_scientific = vmax < 0.01 or value_range > 100

print(f"\nValue statistics:")
print(f"  Min: {vmin:.4e}")
print(f"  Max: {vmax:.4e}")
print(f"  Range factor: {value_range:.1f}x")
print(f"  Using scientific notation: {use_scientific}")

# Create a figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# 1. Expected Deaths Mean
ax1 = axes[0, 0]
from matplotlib.ticker import ScalarFormatter
formatter = ScalarFormatter(useMathText=True)
formatter.set_scientific(True)
formatter.set_powerlimits((-2, 2))

plot1 = gdf.plot(
    column='expected_deaths_mean',
    ax=ax1,
    legend=True,
    cmap='YlOrRd',
    edgecolor='face',  # Edge color matches face color for solid blocks
    linewidth=0.3,
    legend_kwds={
        'label': 'Expected Deaths (Mean)', 
        'shrink': 0.8,
        'format': formatter
    }
)
ax1.set_title('Expected Deaths (Mean)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
ax1.grid(True, alpha=0.3)

# Add text annotation with value range
textstr = f'Range: {vmin:.2e} to {vmax:.2e}'
ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 2. Expected Deaths Standard Deviation
ax2 = axes[0, 1]
vmin_std = gdf['expected_deaths_std'].min()
vmax_std = gdf['expected_deaths_std'].max()

gdf.plot(
    column='expected_deaths_std',
    ax=ax2,
    legend=True,
    cmap='Blues',
    edgecolor='face',  # Edge color matches face color
    linewidth=0.3,
    legend_kwds={
        'label': 'Expected Deaths (Std Dev)', 
        'shrink': 0.8,
        'format': formatter
    }
)
ax2.set_title('Expected Deaths (Standard Deviation)', fontsize=14, fontweight='bold')
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
ax2.grid(True, alpha=0.3)

# Add text annotation
textstr_std = f'Range: {vmin_std:.2e} to {vmax_std:.2e}'
ax2.text(0.02, 0.98, textstr_std, transform=ax2.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

# 3. Risk Coefficient of Variation (uncertainty relative to mean)
gdf['risk_cv'] = gdf['expected_deaths_std'] / (gdf['expected_deaths_mean'] + 1e-10)
ax3 = axes[1, 0]
gdf.plot(
    column='risk_cv',
    ax=ax3,
    legend=True,
    cmap='RdYlGn_r',
    edgecolor='face',  # Solid blocks
    linewidth=0.3,
    legend_kwds={'label': 'Coefficient of Variation', 'shrink': 0.8}
)
ax3.set_title('Risk Uncertainty (CV = Std/Mean)', fontsize=14, fontweight='bold')
ax3.set_xlabel('Longitude')
ax3.set_ylabel('Latitude')
ax3.grid(True, alpha=0.3)

# 4. Number of Occupants
ax4 = axes[1, 1]
gdf.plot(
    column='num_occupants',
    ax=ax4,
    legend=True,
    cmap='viridis',
    edgecolor='face',  # Solid blocks
    linewidth=0.3,
    legend_kwds={'label': 'Number of Occupants', 'shrink': 0.8}
)
ax4.set_title('Number of Occupants', fontsize=14, fontweight='bold')
ax4.set_xlabel('Longitude')
ax4.set_ylabel('Latitude')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
output_path = "../Output/Maps/building_risk_static_maps.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\nStatic maps saved to: {output_path}")

# Create a scatter plot showing mean vs std
fig2, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(
    gdf['expected_deaths_mean'],
    gdf['expected_deaths_std'],
    c=gdf['num_occupants'],
    s=gdf['num_occupants'] * 2,
    alpha=0.6,
    cmap='plasma',
    edgecolors='black',
    linewidth=0.5
)
ax.set_xlabel('Expected Deaths (Mean)', fontsize=12)
ax.set_ylabel('Expected Deaths (Standard Deviation)', fontsize=12)
ax.set_title('Risk Uncertainty Analysis: Mean vs Standard Deviation', 
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Add colorbar for occupants
cbar = plt.colorbar(scatter, ax=ax, label='Number of Occupants')

# Add diagonal reference line (where std = mean)
max_val = max(gdf['expected_deaths_mean'].max(), gdf['expected_deaths_std'].max())
ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Std = Mean')
ax.legend()

output_path2 = "../Output/Maps/risk_uncertainty_scatter.png"
plt.savefig(output_path2, dpi=300, bbox_inches='tight')
print(f"Scatter plot saved to: {output_path2}")

# Print statistics
print("\n" + "="*60)
print("RISK STATISTICS SUMMARY")
print("="*60)
print(f"\nTotal buildings analyzed: {len(gdf)}")
print(f"\nExpected Deaths (Mean):")
print(f"  Min:    {gdf['expected_deaths_mean'].min():.4e}")
print(f"  Max:    {gdf['expected_deaths_mean'].max():.4e}")
print(f"  Mean:   {gdf['expected_deaths_mean'].mean():.4e}")
print(f"  Median: {gdf['expected_deaths_mean'].median():.4e}")
print(f"  Total:  {gdf['expected_deaths_mean'].sum():.4e}")

print(f"\nExpected Deaths (Std Dev):")
print(f"  Min:    {gdf['expected_deaths_std'].min():.4e}")
print(f"  Max:    {gdf['expected_deaths_std'].max():.4e}")
print(f"  Mean:   {gdf['expected_deaths_std'].mean():.4e}")

print(f"\nOccupancy:")
print(f"  Total occupants:     {gdf['num_occupants'].sum():.0f}")
print(f"  Mean per building:   {gdf['num_occupants'].mean():.2f}")
print(f"  Max per building:    {gdf['num_occupants'].max():.0f}")

# Identify high-risk buildings
high_risk_threshold = gdf['expected_deaths_mean'].quantile(0.90)
high_risk_buildings = gdf[gdf['expected_deaths_mean'] >= high_risk_threshold]
print(f"\nHigh-risk buildings (top 10%):")
print(f"  Count: {len(high_risk_buildings)}")
print(f"  Threshold: {high_risk_threshold:.4e}")
print(f"  Total expected deaths: {high_risk_buildings['expected_deaths_mean'].sum():.4e}")

print(f"\nTop 5 Highest Risk Buildings:")
top_5 = gdf.nlargest(5, 'expected_deaths_mean')
for idx, (i, row) in enumerate(top_5.iterrows(), 1):
    print(f"  {idx}. Mean: {row['expected_deaths_mean']:.4e}, Std: {row['expected_deaths_std']:.4e}, Occupants: {row['num_occupants']:.0f}")

plt.show()
