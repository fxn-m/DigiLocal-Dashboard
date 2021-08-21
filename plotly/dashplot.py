import os
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go


wdir = os.getcwd()
datadir = wdir[0:-6]


#app = dash.Dash(__digilocal_choropleth__)

df = pd.read_csv(datadir + '\datasets\selecteddata.csv')