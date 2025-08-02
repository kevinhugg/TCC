import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime

from data.dados import agents, Ocur_Vehicles

dash.register_page(__name__, path='/historic', name='Histórico', className='pg-at')

tipos = sorted(list({item.get('class', '').capitalize() for item in Ocur_Vehicles if 'class' in item}))

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleConfigs.css'),

        dcc.Store(id='filtro-search'),

        html.Div([

            html.Div([
                html.Div([
                    html.Img(src='/static/assets/icons/filter.png', className='icone-filtro')
                ], id='toggle-filtros', n_clicks=0),
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date_placeholder_text="Data inicial",
                        end_date_placeholder_text="Data final",
                        display_format='DD/MM/YYYY',
                        className='date-picker',
                    ),
                    dcc.Dropdown(
                        id='tipo-select',
                        options=[{'label': 'Todos', 'value': 'todos'}] + [
                            {'label': tipo, 'value': tipo.lower()} for tipo in tipos
                        ],
                        value='todos',
                        placeholder='Selecione o tipo',
                        className='tipo-dropdown',
                    )
                ], id='filtros', className='filtro-dropdown-content')
            ], className='filtro-dropdown'),

        ], className='hist-container')

], className='page-content')

@callback(
    Output('filtros', 'className'),
    Input('toggle-filtros', 'n_clicks'),
    State('filtros', 'className'),
    prevent_initial_call=True
)
def toggle_filters(n_clicks, current_class):
    if not current_class:
        current_class = 'filtro-dropdown-content'
    if 'open' in current_class:
        return 'filtro-dropdown-content'
    else:
        return 'filtro-dropdown-content open'