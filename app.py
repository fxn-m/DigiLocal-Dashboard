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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

wdir = os.getcwd()
#data = wdir + '/datasets/selecteddata.csv'
data = wdir + '/datasets/devdata.csv'

df = pd.read_csv(data)
#geojson = wdir + '/datasets/LSOA-2011-GeoJSON/lsoa.geojson'
geojson = wdir + '/datasets/LSOA-2011-GeoJSON/dev_data.geojson'
with open(geojson) as lsoa_file:
    geojson = json.load(lsoa_file)
styles = ['open-street-map','carto-positron']

nomi = pgeocode.Nominatim('GB')

cities_df = pd.read_csv(wdir + '/datasets/cities.csv')

options = []
for i, r in cities_df.iterrows():
    city = r.city
    options.append({'value':city, 'label':city})

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([

    html.Div(
        [

        html.Br(),

        html.Div([
            dcc.Dropdown(
            id='search',
            value='None',
            clearable=True,
            placeholder="Search by Town or City"
            )
        ],
        style={"width":"50%"}
        ),

        html.Div([
            dcc.Input(
            id='postcode',
            placeholder="Search by Postcode"
            )
        ],
        style={"width":"50%"}
        ),

        html.Br(),
        dcc.Graph(id="choropleth", style={'height': '75vh'}),

        html.Div([
        dcc.RadioItems(
            id='mbstyle',
            options=[{'value': x, 'label': x}
            for x in styles],
            value='open-street-map')],
        style={"width": "50%"}),

        html.Br(),
        html.P('IDACI Decile Filter'),
        dcc.RangeSlider(id='rangeslider',
            min=1,
            max=10,
            step=1,
            marks={i: 'Decilie {}'.format(i) for i in range(1, 11)},
            value=[1, 10]
            )
        ],
        style={"width":"65%"})    
]
)

@app.callback(
    Output("search", "options"),
    Input("search", "search_value")
)
def update_options(search):
    if not search:
        raise PreventUpdate
    return [o for o in options if search in o['label']]


@app.callback(
    Output("choropleth", "figure"),
    Input("search", "value"),
    Input("postcode", "value"),
    Input("mbstyle", "value"),
    Input("rangeslider", "value")
    )
def display_choropleth(search, postcode, mbstyle, slider_value):

    dff = df[df['IDACI Decile'].between(slider_value[0], slider_value[1])]

#start map at centre of England to begin with 
    if search == "None":
        centre={
            "lat": 52.36, 
            "lon": -1.17
        }
        zoom = 6
    elif search.isalpha():
        centre={
            "lat": round(cities_df[cities_df.city == search].lat.values[0],2),
            "lon": round(cities_df[cities_df.city == search].lng.values[0],2)
        } 
        zoom = 10
    else:
        splitted = postcode.replace(" ", "")
        final = ''.join(splitted[0:-3] + ' ' + splitted[-3:])
        centre={
            "lat": round(nomi.query_postal_code(final)['latitude'],2),
            "lon": round(nomi.query_postal_code(final)['longitude'],2)
        }
        zoom = 10

#create the map
    fig = px.choropleth_mapbox(
        dff, 
        geojson=geojson, 
        color='IDACI Decile', 
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
