import dash
from dash import html, dcc, Input, Output, callback, State
import dash_daq as daq

from data.dados import agents, Ocur_Vehicles

dash.register_page(__name__, path='/configurations', name='Configurações', className='pg-at')

tipos = sorted(list({item.get('class', '').capitalize() for item in Ocur_Vehicles if 'class' in item}))

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleConfigs.css'),

            html.Div([
                html.H2("Configurações", style={"marginBottom": "10px"}),

                html.Div([
                    html.Div([
                        html.Img(src='/static/assets/icons/darkMode.png', className='icon-config'),
                        html.P("Modo Escuro"),
                    ], className='txt-icon'),
                    html.Div([
                        daq.BooleanSwitch(id='dark-mode-toggle', on=False, size=50)
                    ], className='dark-mode-wrapper')
                ], className='config-item dark-mode-item'),

                html.Div([
                    html.Img(src='/static/assets/icons/about.png', className='icon-config'),
                    html.P("Sobre Nós"),
                ], className='config-item'),

                html.Div([
                    html.Img(src='/static/assets/icons/out.png', className='icon-config'),
                    html.P("Logout"),
                ], className='config-item'),

            ],className="config-list-container"),

],id='page-content',  className='page-content')