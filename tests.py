# import the libraries to be used in this app
import os
import dash
import json
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
from dash.exceptions import PreventUpdate
import pgeocode
from math import radians, cos, sin, asin, sqrt

# import data to be used in this app (see data_cleaning_and_preparation.ipynb)
wdir = os.getcwd()
#df = pd.read_csv(wdir + '/datasets/dashboarddata.csv') #LSOA defined data 
df = pd.read_csv(wdir + '/datasets/devdata.csv') #sample dataset for development 
cities_df = pd.read_csv(wdir + '/datasets/completecitiesandpostcodes.csv') #list of cities and their co-ordinates

# create list of dictionaries to be used in search drop-down
options = []
for i, r in cities_df.iterrows():
    city = r.city
    options.append({'value':city, 'label':city})

#geojson = wdir + '/datasets/LSOA-2011-GeoJSON/lsoa.geojson' #LSOA boundary geometry
geojson = wdir + '/datasets/LSOA-2011-GeoJSON/dev_data.geojson' #sample dataset for development

with open(geojson) as lsoa_file:
    geojson = json.load(lsoa_file)

# set variables for later use
styles = ['open-street-map','carto-positron'] #mapbox options
nomi = pgeocode.Nominatim('GB') #short-hand for post-code library requests
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] #use the css stylesheet from the Dash Tutorial




def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    m = 6371* c *1000
    return m


def setcolour(x):
    if (x < 4) or (x == 8):
        return "#90EE90" #LightGreen
    elif x == 5 or x == 6 or x == 9:
        return "#FFA07A" #LightSalmon
    elif x == 4 or x == 7 or x == 10:
        return "#F08080" #LightCoral


# begin app instance
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([

    html.Div(
        [
            # search field
            html.Br(),
            html.Div(
                [
                    dcc.Dropdown(
                        id='local_authority',
                        options=[{'value': x, 'label': x}
                        for x in df['Local Authority'].unique()],
                        value='Bristol, City of',
                        clearable=False),

                    dcc.Input(
                        style={'width': 300},
                        id='search',
                        placeholder="Search by Postcode, Town, or City",
                        debounce=True,
                        type='search',
                        value=''
                    )
                ]
            ),
            
            html.Div(
                [
                    html.P('IDACI Decile Filter'),
                    dcc.RangeSlider(
                        id='idacislider',
                        min=1,
                        max=10,
                        step=1,
                        marks={i: '{}'.format(i) for i in range(1, 11)},
                        value=[1, 10]),
                    html.P('IUC Code Filter'),
                    dcc.RangeSlider(
                        id='iucslider',
                        min=1,
                        max=10,
                        step=1,
                        marks={i: '{}'.format(i) for i in range(1, 11)},
                        value=[1, 10]),
                ],
                style={"width": "50%"}        
            ),
    
            dcc.RadioItems(
                id='chorofilter',
                options=[
                    {'value':'IDACI Decile', 'label':'IDACI'},
                    {'value':'IUC code','label':'IUC'}
                ],
                value='IDACI Decile'
            ),
    
            html.Hr(),
            dcc.Graph(id="choropleth", style={'height': '75vh'}),
    
            html.Div(
                [
                    dcc.Dropdown(
                        id='mbstyle',
                        options=[{'value': x, 'label': x}
                        for x in styles],
                        value='open-street-map',
                        clearable=False)
                ],
                style={"width": "25%"}
            ),

            html.Div(id="number-output")
        ],
        style={"width":"65%"}
    )    
]
)

@app.callback(
    Output("choropleth", "figure"),
    Input("local_authority", "value"),
    Input("search", "value"),
    Input("mbstyle", "value"),
    Input("idacislider", "value"),
    Input("iucslider", "value"),
    Input("chorofilter", "value")
    )
def display_choropleth(local_authority, search, mbstyle, idaci_slider_value, iuc_slider_value, chorofilter):
    filtered_by_la = df[df['Local Authority'] == local_authority]
    filtered_by_idaci = filtered_by_la[filtered_by_la['IDACI Decile'].between(idaci_slider_value[0], idaci_slider_value[1])]
    filtered_by_iuc = filtered_by_idaci[filtered_by_idaci['IUC code'].between(iuc_slider_value[0], iuc_slider_value[1])]

#start map at centre of England to begin with, set centre to the co-ordinates associated with the search input 
    if search == "":
        centre={
            "lat": 52.36, 
            "lon": -1.17
        }
        zoom = 6
    elif ~(not search) and search.isalpha():
        centre={
            "lat": round(cities_df[cities_df.city == search.title()].lat.values[0],2),
            "lon": round(cities_df[cities_df.city == search.title()].lng.values[0],2)
        } 
        zoom = 10
    else:
        splitted = search.replace(" ", "")
        final = ''.join(splitted[0:-3] + ' ' + splitted[-3:])
        centre={
            "lat": round(nomi.query_postal_code(final)['latitude'],2),
            "lon": round(nomi.query_postal_code(final)['longitude'],2)
        }
        zoom = 12

#create the map
    fig = px.choropleth_mapbox(
        filtered_by_iuc, 
        geojson=geojson, 
        color=chorofilter, 
        color_continuous_scale="Viridis",
        locations="LSOA code", 
        featureidkey="properties.LSOA11CD",
        hover_name='Local Authority',
        center=centre, 
        zoom=zoom,
        range_color=[0, 10], 
        opacity=.5)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style=mbstyle)

    return fig



@app.callback(
    Output("number-output", "children"),
    Input("choropleth", "clickData"), #lsoa code from clicked tile
    )

def update_output(clickData):
    if clickData is not None:
        return clickData['points'][0]['location']
    
if __name__ == '__main__':
    app.run_server(debug=True)
