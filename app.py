import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import pymongo
import helper_functions
import re
import csv

"""
TABLE OF CONTENTS

I. SETTING UP DATA AND DEFINING GLOBAL VARIABLES
II. APP LAYOUT
III. CALLBACKS
"""



"""
I. SETTING UP DATA AND DEFINING GLOBAL VARS
-----------------------------------------
"""



state_abbrevs = open('state-abbreviations.csv')
state_abbrevs_reader = csv.reader(state_abbrevs)
state_abbrevs_dict = dict(state_abbrevs_reader)

# Load sustainability df
states_data = helper_functions.get_states_data()

# Store names of all possible sectors
sectors = states_data['Alabama'].keys()

sus_df = helper_functions.get_sustainability_df()

si_range = np.arange(0.0, 1.1, 0.1)
si_range = np.round(si_range,1)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

title_md = '''
### U.S. Energy Consumption Trends
'''
consumption_md = '#### Consumption at a Glance'

si_md= '''
Hover over a state to view its energy consumption from 1960-2017. The slider below the map \
calculates the Sustainability Index for each state, which is a weighted combination of its Effort and Green Scores.

**Effort Score**: a measure of *change* in a state's nonrenewable energy consumption (NEC) relative to its renewable energy consumption (REC) from 2000-2017.

**Green Score**: a measure of how *close* a state's NEC and REC are from 2000-2017.

An index of 1 represents highest ranking sustainability metrics across current U.S. states.

'''

breakdown_md = '#### Energy Consumption Breakdown: Sector and Fuel Type'

dropdown_md= 'Select a state and an energy source to view a breakdown of consumption across sectors and constituent fuel types.'

radio_md='View energy breakdown by:'



"""
II. APP LAYOUT
----------------
"""



app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.Div(
            [
                dcc.Markdown(title_md)
            ],
            style={
                #'textAlign': "center",
                'borderBottom': 'thin lightgrey solid',
                # 'backgroundColor': 'rgb(0,168,84)',
                'textColor':'white',
                'padding': '10px 5px'
            }
        ),
        html.Div(
            dcc.Markdown(consumption_md),
            style={'textAlign': "center"}
        ),

        # Map and Slider
        html.Div(
            [
                dcc.Graph(
                    id="crossfilter_map_with_slider",
                    hoverData={'points':'data'},
                    ),

                html.Div(
                    dcc.Slider(
                        id='si_slider',
                        min=si_range.min(),
                        max=si_range.max(),
                        value=si_range.max(),
                        step=0.1
                        )
                    ),

                html.Div(
                    dcc.Markdown(
                        id='updatemode-output-container',
                        style={
                            'margin-bottom': 10,
                            'textAlign':'center',
                            'display':'inline-block'
                        }
                    )
                )
            ],
            style={'width': '50%', 'display': 'inline-block'}
        ),
        # Instructions + at a glance graph
        html.Div(
            [
                dcc.Markdown(si_md),
                dcc.Graph(id="total_all_sec_ts")
            ],
            style={
                'width': '50%',
                'display': 'inline-block',
                'vertical-align': 'top'
            }
        ),
        # Explanations for following graphs + Dropdown + checkboxes
        html.Div(
            dcc.Markdown(breakdown_md),
            style={
                'textAlign': "center",
                'borderTop': 'thin lightgrey solid'
            }
        ),
        html.Div(
            [
                dcc.Markdown(dropdown_md),
                html.Div(
                    [
                        dcc.Dropdown(
                            id='state_dropdown',
                            options=[
                                {
                                    'label':state_abbrevs_dict[state],
                                    'value':state_abbrevs_dict[state]
                                }
                                for state in state_abbrevs_dict
                            ],
                            value="New York"
                        )
                    ],
                    style={
                        'margin-right': 20,
                        'margin-bottom':10,
                        'margin-top':10
                    }
                ),
                dcc.Markdown(radio_md),
                dcc.RadioItems(
                    id='source_radio_item',
                    options=[
                        {'label': 'Sector', 'value': 'sector'},
                        {'label': 'Fuel', 'value': 'fuel'}
                    ],
                    value='sector'
                ),
                html.Div(
                    dcc.Markdown(
                        id='scores_md',
                        style={
                            # 'width':'50%',
                            # 'margin-top': 10,
                            # 'textAlign':'center',
                            'display':'inline-block'
                        }
                    ),
                    style={
                        # 'margin-top':5,
                        'display':'inline-block'
                    }
                ),
            ],
            style={
                'width': '40%',
                'display':'inline-block',
                'vertical-align': 'top'
            }
        ),
        # Sector and fuel breakdown time-series graphs
        html.Div(
            [
                dcc.Graph(id="sectors_ts"),
                dcc.Graph(id="fuels_ts")
            ],
            style={
                'width': '60%',
                'display': 'inline-block'
            }
        )
    ],
    style={
        'padding':'0px 20px',
        # 'background-color':'rgb(240, 240, 240)'
    }
)



"""
III. CALLBACKS
---------------
"""



@app.callback(
    dash.dependencies.Output('crossfilter_map_with_slider', 'figure'),
    [dash.dependencies.Input('si_slider', 'value')]
    )

def update_figure(selected_si):

    if selected_si == 0:
        selected_si = '0.0'
    elif selected_si == 1:
        selected_si = '1.0'

    column = 'SI_'+ str(selected_si)

    trace = go.Choropleth(
        locations=sus_df['code'],
        z=sus_df[column].astype(float),
        locationmode='USA-states',
        colorscale='Greens',
        autocolorscale=False,
        # hovertext=sus_df['text'], # hover text
        marker_line_color='white', # line markers between states
        colorbar={"thickness": 10,"len": 0.55,"x": 0.9,"y": 0.55,'outlinecolor':'white',
                  'title': {#"text": 'SI',
                            "side": "top"}}
        )

    return {"data": [trace],
            "layout": go.Layout(title={'text':'Sustainability Indexes of U.S. States',
                                        'y':0.95,
                                        },
                                height=500,
                                geo = dict(
                                    scope='usa',
                                    projection=go.layout.geo.Projection(type = 'albers usa'),
                                    showlakes=False, # lakes
                                    ),
                                margin={'t':0,'b':0,'l':10,'r':10})}

def create_timeseries(hoverData, case, title, sources, state):
    """
    There are three cases for time series plots:
    1) Both sources (renewable & nonrenewable) for 'Total All Sectors'
    2) One source for all sectors
    3) All fuel types that make up one source for 'Total All Sectors' (could later expand to choosing sector)
    """
    assert case in [1, 2, 3], "Make sure to select one of 3 possible cases: 1, 2, or 3"

    if hoverData['points'] == 'data':
            state_code = 'NY'
    else:
        state_code = hoverData['points'][0]['location']





    line_colors = {'Nonrenewable Sources' : 'rgb(255,128,0)',
                     'Renewable Sources' : 'rgb(0,168,84)'}

    trace = []

    if case == 1:
        height = 350
        state = state_abbrevs_dict[state_code]
        xaxis_range = ['1960-01-01', '2017-01-01']
        for source in sources:

            trace.append(go.Scatter(
                                    x=states_data[state]['Total All Sectors'].index,
                                    y=states_data[state]['Total All Sectors'][source],
                                    name=source.split()[0],
                                    line_color=line_colors[source]
                                    )
                        )
    if case == 2:
        height = 300
        xaxis_range=['2000-01-01', '2017-01-01']
        for sector in sectors:

            trace.append(go.Scatter(
                                    x=states_data[state][sector].index,
                                    y=states_data[state][sector][sources[0]],
                                    name=re.findall('(.*)( [Sectors]*)$',sector)[0][0]
                                    )
                        )
    elif case == 3:
        height = 300
        xaxis_range=['2000-01-01', '2017-01-01']
        if sources[0] == 'Renewable Sources':
            energy_types = ['Renewable Sources'] + helper_functions.renewable_sources
            # energy_types.append('Renewable Sources')
        elif sources[0] == 'Nonrenewable Sources':
            energy_types = ['Nonrenewable Sources'] + helper_functions.nonrenewable_sources
            # energy_types.append('Nonrenewable Sources')

        for energy_type in energy_types:
            if energy_type == 'Renewable Sources':
                name = 'All Renewable'
            elif energy_type == 'Nonrenewable Sources':
                name = 'All Nonrenewable'
            else:
                name = re.findall('(\w* ?\w*)',energy_type)[0]

            trace.append(go.Scatter(
                                    x=states_data[state]['Total All Sectors'].index,
                                    y=states_data[state]['Total All Sectors'][energy_type],
                                    name=name
                                    )
                        )

    title = state + ' ' + title

    layout = go.Layout(dict(
                        title = title,
                        template = "plotly_white",
                        margin={'t':70,'l':60,'b':40},
                        xaxis_title = 'Year',
                        yaxis_title = 'Energy Consumption<br>(Billion Btu)',
                        xaxis_showgrid=False,
                        yaxis_ticks='outside',
                        yaxis_tickcolor='white',
                        yaxis_ticklen=10,
                        yaxis_zeroline=True,
                        # legend={'orientation':'h',},
                        xaxis_range=xaxis_range,
                        height = height,  #600
                        ))

    return {'data':trace,'layout':layout}


@app.callback(
    dash.dependencies.Output('total_all_sec_ts', 'figure'),
    [dash.dependencies.Input('crossfilter_map_with_slider', 'hoverData')])

def update_total_all_sec_ts(hoverData):
    case = 1
    title = 'Energy Consumption at a Glance'
    sources = ['Nonrenewable Sources', 'Renewable Sources']
    state = None

    return create_timeseries(hoverData, case, title, sources, state)


@app.callback(
    dash.dependencies.Output('sectors_ts', 'figure'),
    [dash.dependencies.Input('crossfilter_map_with_slider', 'hoverData'),
     dash.dependencies.Input('state_dropdown', 'value'),
     dash.dependencies.Input('source_radio_item', 'value')
     ])

def update_sectors_ts(hoverData, state, source):
    if source == 'sector':
        case = 2
        title = 'Renewable Energy Consumption by Sector'
    elif source == 'fuel':
        case = 3
        title = 'Renewable Energy Consumption for All Sectors by Fuel'

    sources = ['Renewable Sources']

    return create_timeseries(hoverData, case, title, sources, state)


@app.callback(
    dash.dependencies.Output('fuels_ts', 'figure'),
    [dash.dependencies.Input('crossfilter_map_with_slider', 'hoverData'),
     dash.dependencies.Input('state_dropdown', 'value'),
     dash.dependencies.Input('source_radio_item', 'value')])

def update_fuels_ts(hoverData, state, source):
    if source == 'sector':
        case = 2
        title = 'Nonrenewable Energy Consumption by Sector'
    elif source == 'fuel':
        case = 3
        title = 'Nonrenewable Energy Consumption for All Sectors by Fuel'

    sources = ['Nonrenewable Sources']
    return create_timeseries(hoverData, case, title, sources, state)

@app.callback(Output('updatemode-output-container', 'children'),
              [Input('si_slider', 'value')])

def display_value(value):
    gs_percent = round((1-value)*100,1)
    es_percent = round((value)*100,1)
    return f'Sustainability Index: Green Score: {gs_percent}% | Effort Score: {es_percent}%'

@app.callback(Output('scores_md', 'children'),
              [Input('state_dropdown', 'value')])

def display_gs(value):
    gs = sus_df.loc[value]['Green Score']
    es = sus_df.loc[value]['Effort Score']
    return f'''
    ##### {value} Sustainability Scores
    Effort Score: {es}

    Green Score: {gs}

    '''

if __name__ == '__main__':
    app.run_server(debug=True)
