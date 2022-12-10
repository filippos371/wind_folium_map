# importing packages
import pathlib
import pandas as pd
import geopandas as gcp
import numpy as np
import folium 
from folium.plugins import Search
import branca

# read geojson files
gs=gcp.read_file('./data/temp_geo.geojson')
print(gs.columns)

#Read wind parks data------------------------ #
# Read Wind parks data with operation licenses
ff_name='wind_operation_data.csv'  
df_operation=pd.read_csv(f"./data/{ff_name}")

# Read Wind parks data with production licenses
ff_name='wind_production_data.csv'  
df_prod=pd.read_csv(f"./data/{ff_name}")

# Pivot sums per region for Operation licenses
df_sums_op=pd.pivot_table(df_operation,index=['kal_perifereia'],values='power_mw',aggfunc='sum').reset_index(drop=False)
df_sums_op.rename(columns={'kal_perifereia':'PER'},inplace=True)
df_sums_op.rename(columns={'power_mw':'wind_cap_op'},inplace=True)

# Pivot sums per region for Production licenses
df_sums_prod=pd.pivot_table(df_prod,index=['kal_perifereia'],values='power_mw',aggfunc='sum').reset_index(drop=False)
df_sums_prod.rename(columns={'kal_perifereia':'PER'},inplace=True)
df_sums_prod.rename(columns={'power_mw':'wind_cap_prod'},inplace=True)

# Merge wind data with geojson file 
gs_op=gs.merge(df_sums_op[['PER','wind_cap_op']],on='PER',how='left')
gs_last=gs_op.merge(df_sums_prod[['PER','wind_cap_prod']],on='PER',how='left')
#gs_last['wind_cap_op']=[int(x) for x in gs_last['wind_cap_op']]
#gs_last['wind_cap_prod']=[int(x) for x in gs_last['wind_cap_prod']]
gs_last['wind_cap_op_label']=[f"{int(x)} MW" for x in gs_last['wind_cap_op']]
gs_last['wind_cap_prod_label']=[f"{int(x)} MW" for x in gs_last['wind_cap_prod']]
print(gs_last.head(2))


# -------------------------------------------------------------------- #
# CREATE MAP --------------------------------------------------------- #

# SET COLORS --------------------------------------------------------- #
# We set the colormap's highest value the one of productions licenses,
# because it will be at least the same as in operation licenses
colorscale_op = branca.colormap.linear.OrRd_09.scale(0, gs_last['wind_cap_prod'].max(),max_labels=20)
colorscale_prod = branca.colormap.linear.OrRd_09.scale(0, gs_last['wind_cap_prod'].max())

colorscale_op.caption="Wind capcity with operation license (MW)"
colorscale_prod.caption="Wind capcity with production license (MW)"
colorscale_op.tick_labels=list(np.arange(0,6000,750))+[gs_last['wind_cap_prod'].max()]
colorscale_prod.tick_labels=colorscale_op.tick_labels


m = folium.Map(location=[38.526682,22.27478 ],zoom_start=7,overlay=False,tiles=None)
folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(m)
# Plot wind capacity under different type of licenses (Operation vs Production licenses)
fg1 = folium.FeatureGroup(name='Wind Capacity with Op.License (MW)',overlay=False).add_to(m)
fg2 = folium.FeatureGroup(name='Wind Capacity with Prod.License (MW)',overlay=False).add_to(m)

points_op = folium.FeatureGroup(name='Wind parks with Op.License',overlay=False).add_to(m)
points_prod = folium.FeatureGroup(name='Wind parks with Prod.License',overlay=False).add_to(m)



def wind_style_func(var_name='wind_cap_prod'):
    return lambda x: {'fillColor': colorscale_op(x['properties'][var_name]),
                      'fillOpacity':0.7,
                      'color': 'black',
                      'weight':0.1,
}

# Add wind data into the map
wind_cap_op= folium.GeoJson(gs_last,
                          name='wind_cap_op',
                          tooltip=folium.GeoJsonTooltip(fields=['PER', 'wind_cap_op_label', 'wind_cap_prod_label'], 
                                            aliases=['Region', 'Wind capacity with Operation License', 'Wind capacity with Production license'], 
                                            localize=True),
                         style_function=wind_style_func(var_name='wind_cap_op'),
                         highlight_function=lambda x: {'fillColor':'grey','weight':0.1}
                         ).add_to(fg1)

wind_cap_prod = folium.GeoJson(gs_last,
                          name='wind_cap_prod',
                          tooltip=folium.GeoJsonTooltip(fields=['PER', 'wind_cap_op_label', 'wind_cap_prod_label'], 
                                            aliases=['Region', 'Wind Op. Cap.', 'Wind Prod. Cap.'], 
                                            localize=True),
                          style_function=wind_style_func(var_name='wind_cap_prod'),
                          highlight_function=lambda x: {'fillColor':'grey','weight':0.1}
                         ).add_to(fg2)


# Add points
def popup_fun(x):
    temp_date=f"<p><b>Lin. date: {x['imerominia_ekdosis_adeias']}</b></p>"
    temp_power=f"<p><b>Power(MW): {x['power_mw']}</b></p>"
    return temp_date+temp_power

for ind,xx in df_operation.iterrows():    
    tooltip = "Click me!"
    temp_popup=popup_fun(xx)    
    folium.Circle([xx['xmu'],xx['ymu']], popup=temp_popup, tooltip=tooltip,fill=True,radius=200).add_to(points_op)
    #folium.Marker([xx['xmu'],xx['ymu']], popup=temp_popup, tooltip=tooltip).add_to(m)
    
for ind,xx in df_prod.iterrows():    
    tooltip = "Click me!"
    temp_popup=popup_fun(xx)    
    folium.Circle([xx['xmu'],xx['ymu']], popup=temp_popup, tooltip=tooltip,fill=True,radius=200).add_to(points_prod)
    #folium.Marker([xx['xmu'],xx['ymu']], popup=temp_popup, tooltip=tooltip).add_to(m)
    


# Add search bar
reg_search = Search(layer=wind_cap_op, 
                      geom_type='Polygon', 
                      placeholder="Search for a State", 
                      collapsed=True, 
                      search_label='PER',
                      weight=2
                    ).add_to(m)


# Add color bar
colorscale_op.add_to(m)

# Add Tiles 
folium.TileLayer('openstreetmap',overlay=True,name="View map features").add_to(m)
folium.TileLayer('cartodbdark_matter',overlay=True,name="View in Dark Mode").add_to(m)
folium.TileLayer('cartodbpositron',overlay=True,name="Viw in Light Mode").add_to(m)


# Add layer control
folium.LayerControl().add_to(m)
# Save as HTML
m.save('map.html')

# -------------------------------------------------------------------- #

