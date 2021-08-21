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
geojson = wdir + '/datasets/LSOA-2011-GeoJSON/lsoa.geojson'
with open(geojson) as lsoa_file:
    geojson = json.load(lsoa_file)
styles = ['open-street-map', 'white-bg', 'carto-positron', 
'carto-darkmatter', 'stamen- terrain', 'stamen-toner', 'stamen-watercolor']

app.layout = html.Div([
    dcc.Dropdown(
    id='mbstyle',
    options=[{'value': x, 'label': x}
             for x in styles],
    value='carto-positron'
    ),

    dcc.Graph(id="choropleth", style={'height': '75vh'}),

    html.Br(),
    html.P('Filter for Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)'),
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
    Input("rangeslider", "value")
    )
def display_choropleth(mbstyle, slider_value):
    dff = df[df['IDACI Decile'].between(slider_value[0], slider_value[1])]
    fig = px.choropleth_mapbox(
        dff, geojson=geojson, color='IDACI Decile', color_continuous_scale="Viridis",
        locations="LSOA code", featureidkey="properties.LSOA11CD",
        hover_name='Local Authority District name',
        center={"lat": 53, "lon": -4.5}, zoom=5,
        range_color=[0, 10], opacity=.5)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style=mbstyle)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
    