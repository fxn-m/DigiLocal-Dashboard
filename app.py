import os
import dash
import json
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server
wdir = os.getcwd()
#data = wdir + '/datasets/selecteddata.csv'
data = wdir + '/datasets/devdata.csv'

df = pd.read_csv(data)
#geojson = wdir + '/datasets/LSOA-2011-GeoJSON/lsoa.geojson'
geojson = wdir + '/datasets/LSOA-2011-GeoJSON/dev_data.geojson'
with open(geojson) as lsoa_file:
    geojson = json.load(lsoa_file)
styles = ['open-street-map', 'white-bg', 'carto-positron', 
'carto-darkmatter', 'stamen- terrain', 'stamen-toner', 'stamen-watercolor']

bris = ['Bristol', [51.47, -2.61]]
ldn = ['London', [51.514, -0.1225]]
cities_df = pd.DataFrame(data=[bris, ldn], columns=['city', 'coords'])

app.layout = html.Div([
    dcc.Dropdown(
    id='mbstyle',
    options=[{'value': x, 'label': x}
             for x in styles],
    value='open-street-map'
    ),

    dcc.Dropdown(
    id='city',
    options=[{'value': 'Bristol', 'label': 'Bristol'},
    {'value': 'London', 'label': 'London'}],
    value='Bristol'
    ),

    dcc.Graph(id="choropleth", style={'height': '75vh'}),

    html.Br(),

    html.P('IDACI Decile Filter'),
    dcc.RangeSlider(id='rangeslider',
        min=1,
        max=10,
        step=1,
        marks={i: 'Decilie {}'.format(i) for i in range(1, 11)},
        value=[1, 10]
        )
])

@app.callback(
    Output("choropleth", "figure"),
    Input("mbstyle", "value"),
    Input("rangeslider", "value"),
    Input("city", "value")
    )
def display_choropleth(mbstyle, slider_value, city):
    dff = df[df['IDACI Decile'].between(slider_value[0], slider_value[1])]
    fig = px.choropleth_mapbox(
        dff, geojson=geojson, color='IDACI Decile', color_continuous_scale="Viridis",
        locations="LSOA code", featureidkey="properties.LSOA11CD",
        hover_name='Local Authority',
        #center={"lat": 53, "lon": -4.5}, zoom=5,
        center={"lat": list(cities_df[cities_df.city == city].coords)[0][0], 
        "lon": list(cities_df[cities_df.city == city].coords)[0][1]}, zoom=11,
        range_color=[0, 10], opacity=.5)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style=mbstyle)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
    