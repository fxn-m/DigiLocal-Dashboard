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

# import data to be used in this app (see data_cleaning_and_preparation.ipynb)
wdir = os.getcwd()
#df = pd.read_csv(wdir + '/datasets/selecteddata.csv') #LSOA defined data 
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
                    dcc.RadioItems(
                        id='mbstyle',
                        options=[{'value': x, 'label': x}
                        for x in styles],
                        value='open-street-map')
                ],
                style={"width": "50%"}
            ),
        ],
        style={"width":"65%"}
    )    
]
)

@app.callback(
    Output("choropleth", "figure"),
    Input("search", "value"),
    Input("mbstyle", "value"),
    Input("idacislider", "value"),
    Input("iucslider", "value"),
    Input("chorofilter", "value")
    )
def display_choropleth(search, mbstyle, idaci_slider_value, iuc_slider_value, chorofilter):

    dff = df[df['IDACI Decile'].between(idaci_slider_value[0], idaci_slider_value[1])]
    dff = dff[dff['IUC code'].between(iuc_slider_value[0], iuc_slider_value[1])]

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
        dff, 
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


if __name__ == '__main__':
    app.run_server(debug=True)
