import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd

import plotly.graph_objs as go
import numpy as np
import pymongo
import helper_functions
import re
import csv

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



navbar = dbc.NavbarSimple(
    children=
        [
            dbc.Button("Learn More", id="learn_more"),
            dbc.Modal(
            [
                dbc.ModalHeader("Welcome"),
                dbc.ModalBody(dcc.Markdown(
                """\
Move the slider below the map to adjust the weight of the Effort Score and
Green Score in calculating the Sustainability Index for a state. This will
update the map, which can be hovered over to view the energy consumption
of a given state since 1960.

Sustainability Index: a weighted average of the Effort Score and Green Score
of a particular state. The user defines the weights of each of the two
component scores.

Effort Score: a measure of how much a state's nonrenewable and renewable energy
consumption converge from 2000-2017.

Green Score: a measure of the average ratio of renewable energy consumption to
nonrenewable energy consumption from 2000-2017.


Scroll down the page for a breakdown of a given state's energy consumption
by sector and fuel type.
                """)
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
            centered=True
        ),
        ],
    brand="U.S. Energy Consumption Trends",
    # brand_href="#",
    dark=True,
    sticky="top",
    color='rgb(0,168,84)'
)

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
body = dbc.Container(
    [
        dbc.Row(
            [
                html.H4('Sustainability at a Glance')
            ],
            justify='center',
            style={
                'padding':'15px 0px'
            }
        ),
        dbc.Row(
            [
                dbc.Col(
                    [

                        dcc.Graph(
                            id="crossfilter_map_with_slider",
                            hoverData={'points':'data'},
                            ),

                        dcc.Slider(
                            id='si_slider',
                            min=si_range.min(),
                            max=si_range.max(),
                            value=si_range.max(),
                            step=0.1
                        ),
                        html.P(
                            id='updatemode-output-container',
                            style={
                                'margin-bottom': 10,
                                'textAlign':'center',
                                'display':'inline-block'
                            }
                        )

                    ],
                    width=5,

                ),
                dbc.Col(
                    [
                        dcc.Graph(id="total_all_sec_ts")
                    ],
                    align='center'
                )
            ]
        ),
        dbc.Row(
            [
                html.H4('Energy Consumption Breakdown: Sector and Fuel Type')
            ],
            justify='center',
            style={
                'padding':'15px 0px'
            }
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P('Select a state.'),
                        dcc.Dropdown(
                            id='state_dropdown',
                            options=[
                                {
                                    'label':state_abbrevs_dict[state],
                                    'value':state_abbrevs_dict[state]
                                }
                                for state in state_abbrevs_dict
                            ],
                            value="New York",
                            # style={'margin-top':'10', 'margin-bottom':'10'}
                        ),
                        html.P(
                            children='View energy breakdown by:',
                            style={
                                'padding':'10px 0px 0px 0px'
                            }
                        ),
                        dbc.RadioItems(
                            id='source_radio_item',
                            options=[
                                {'label': ' Sector ', 'value': 'sector'},
                                {'label': ' Fuel ', 'value': 'fuel'}
                            ],
                            value='sector'
                        ),
                        html.H5(
                            children='New York Sustainability Scores',
                            style={'padding':'30px 0px 0px 0px'}

                        ),
                        html.P(
                            id='scores_text',
                            style={
                                # 'width':'50%',
                                # 'padding': '10px 0px',
                                # 'textAlign':'center',
                                'display':'inline-block'
                            }
                        )
                    ],
                    width=4
                ),
                dbc.Col(
                    [
                        dcc.Graph(id="sectors_ts"),
                        dcc.Graph(id="fuels_ts")
                    ],
                )
            ]
        )
    ],
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([navbar, body])

@app.callback(
    Output("modal", "is_open"),
    [Input("learn_more", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

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
                                        'y':0.9,
                                        },
                                height=350,
                                geo = dict(
                                    scope='usa',
                                    projection=go.layout.geo.Projection(type = 'albers usa'),
                                    showlakes=False, # lakes
                                    ),
                                margin={'t':10,'b':0,'l':10,'r':10})}

@app.callback(Output('updatemode-output-container', 'children'),
              [Input('si_slider', 'value')])

def display_value(value):
    gs_percent = round((1-value)*100,1)
    es_percent = round((value)*100,1)
    return f'Sustainability Index: Green Score: {gs_percent}% | Effort Score: {es_percent}%'

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
        xaxis_range = [1960,2017]
        for source in sources:

            trace.append(go.Scatter(
                                    x=states_data[state]['Total All Sectors'].index.year,
                                    y=round(states_data[state]['Total All Sectors'][source]/1_000_000,2),
                                    name=source.split()[0],
                                    line_color=line_colors[source]
                                    )
                        )
    if case == 2:
        height = 300
        xaxis_range=[2000, 2017]
        for sector in sectors:

            trace.append(go.Scatter(
                                    x=states_data[state][sector].index.year,
                                    y=round(states_data[state][sector][sources[0]]/1_000_000,2),
                                    name=re.findall('(.*)( [Sectors]*)$',sector)[0][0]
                                    )
                        )
    elif case == 3:
        height = 300
        xaxis_range=[2000, 2017]
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
                                    x=states_data[state]['Total All Sectors'].index.year,
                                    y=round(states_data[state]['Total All Sectors'][energy_type]/1_000_000,2),
                                    name=name
                                    )
                        )

    title = state + ' ' + title

    layout = go.Layout(dict(
                        title = title,
                        template = "plotly_white",
                        margin={'t':70,'l':60,'b':40},
                        xaxis_title = 'Year',
                        yaxis_title = 'Energy Consumption (10<sup>15</sup> Btu)',
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
    title = 'Energy Consumption'
    sources = ['Nonrenewable Sources', 'Renewable Sources']
    state = None

    return create_timeseries(hoverData, case, title, sources, state)

@app.callback(Output('scores_text', 'children'),
              [Input('state_dropdown', 'value')])

def display_gs(value):
    gs = sus_df.loc[value]['Green Score']
    es = sus_df.loc[value]['Effort Score']
    return f'Green Score {gs} | Effort Score: {es}'

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

if __name__ == '__main__':
    app.run_server(debug=True)
