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

from functions import haversine
from functions import setcolour

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

#import geojson data
#geojson = wdir + '/datasets/LSOA-2011-GeoJSON/lsoa.geojson' #LSOA boundary geometry
geojson = wdir + '/datasets/LSOA-2011-GeoJSON/dev_data.geojson' #sample dataset for development

with open(geojson) as lsoa_file:
    geojson = json.load(lsoa_file)

# set variables for later use
styles = ['open-street-map','carto-positron'] #mapbox options
nomi = pgeocode.Nominatim('GB') #short-hand for post-code library requests
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] #use the css stylesheet from the Dash Tutorial


# initialise app instance
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(
    [
        html.H1('DigiLocal Dashboard'),
        html.Div([
            html.Div(
                [
                    dcc.Dropdown(
                        id='local_authority',
                        options=[{'value': x, 'label': x}
                        for x in df['Local Authority'].unique()],
                        value='Bristol, City of',
                        clearable=False,
                        style={"width":"97%"}
                    )
                ],
                style={#"width":"49%",
                "margin-top":27,
                "margin-bottom":4}
            ),

            html.Div(
                [
                    dcc.Input(
                        id='search',
                        placeholder="Search by Postcode, Town, or City",
                        debounce=True,
                        type='search',
                        value='',
                        style={"width":400}
                    )
                ]
            )
        ],
        style={
            "display":"inline-block",
            "verticalAlign": "top",
            "width":"49%"
        }, 
        id='search_fields'
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
            
            style={
                "display":"inline-block",
                "verticalAlign": "top",
                "width":"49%"
        },
        id='filters'         
        ),



        html.Hr(),

        html.Div([
        dcc.Graph(id="choropleth", 
            style={'height': '50vh'},
            clickData={'points': [{'location':'E01033359'}]})
        ], 
        style={
            "width":"49%",
            "display":"inline-block",
            "verticalAlign": "top"}
        ),

        html.Div([
            dcc.Graph(
                id="scatter",
                ),
        ],
        style={
            "width":"49%",
            "display":"inline-block",
            "verticalAlign": "top"}),

        html.Div(
            [
                dcc.Dropdown(
                    id='mbstyle',
                    options=[{'value': x, 'label': x}
                    for x in styles],
                    value='open-street-map',
                    clearable=False)
            ],
            style={"width": "25%",
            "margin-top":10}
        ),

        html.Div([
            dcc.RadioItems(
            id='chorofilter',
            options=[
                {'value':'IDACI Decile', 'label':'IDACI'},
                {'value':'IUC code','label':'IUC'}
            ],
            value='IDACI Decile'
            )
        ])


    ],
    style={"width":"65%"}
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

#initialise map on the Engine Shed, Bristol. Then set centre to the co-ordinates associated with the search input 
    if search == "":
        centre={
            "lat": 51.44, 
            "lon": -2.58
        }
        zoom = 11
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
    Output("scatter", "figure"),
    Input("choropleth", "clickData") #lsoa code from clicked tile
    )

def display_scatter(clickData):
    temp = df
    lsoa=clickData['points'][0]['location']
    idx=temp[temp['LSOA code'] == lsoa].index[0]
    selected=temp.loc[idx]
   
    deltas=[]
    for i, r in temp.iterrows():
        delta = haversine(selected['lng'], selected['lat'], r['lng'], r['lat'])
        deltas.append(delta)
    temp['deltas'] = deltas

    temp.sort_values(by='deltas', inplace=True)
    temp.reset_index(inplace=True)
    temp.drop('index', axis=1, inplace=True)
    temp.drop([0], inplace=True)

    data = temp.loc[0:25]

    fig = px.scatter(data_frame=data,
                 x='deltas',
                 y='IDACI Decile',
                 labels={'deltas':'Distance from selected LSOA (m)', 'IDACI Decile':'IDACI Decile'},
                 hover_name='LSOA code',
                 hover_data=['IDACI Decile', 'IUC code', 'IUC classification'],
                 #color=list(map(setcolour, temp.loc[0:25]['IUC code'])),
                 width=700
                 
    )

    fig.update_traces(mode='markers',
                     marker=dict(
                         size=14,
                         color=list(map(setcolour, data['IUC code']))
                     )
                     )
    return fig
    
if __name__ == '__main__':
    app.run_server(debug=True)
