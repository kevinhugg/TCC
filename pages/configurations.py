import dash
from dash import html, dcc, Input, Output, callback, State
import dash_daq as daq
import dash_bootstrap_components as dbc

from data.dados import agents, Ocur_Vehicles

dash.register_page(__name__, path='/configurations', name='Configurações', className='pg-at')

layout = html.Div([
    html.Link(rel='stylesheet', href='/static/css/global.css'),  
    html.Link(rel='stylesheet', href='/static/css/styleConfigs.css'),
    dcc.Store(id='theme-mode', storage_type='local', data='light'),

    html.Div([
        html.H2("Configurações", style={"marginBottom": "10px", "color": "var(--primary-text-color)"}),

        html.Div([
            html.Div([
                html.Img(src='/static/assets/icons/tema.svg', className='icon-config', 
                        style={"filter": "var(--icon-filter)"}),
                html.P("Tema da Aplicação", style={"color": "var(--primary-text-color)"}),
            ], className='txt-icon'),
            html.Div([
                html.Div([
                    html.Div([
                        html.Img(
                            src='/static/assets/icons/darkMode.png',
                            style={
                                'width': '30px',
                                'height': '30px',
                                'filter': 'var(--icon-filter)',
                                'cursor': 'pointer'
                            },
                            id='theme-light-btn'
                        ),
                        html.P('Claro', style={
                            'margin': '5px 0 0 0',
                            'fontSize': '12px',
                            'color': 'var(--primary-text-color)',
                            'textAlign': 'center'
                        })
                    ], style={
                        'display': 'flex',
                        'flexDirection': 'column',
                        'alignItems': 'center',
                        'padding': '10px',
                        'border': '2px solid transparent',
                        'borderRadius': '8px',
                        'margin': '0 5px',
                        'cursor': 'pointer',
                        'backgroundColor': 'var(--card-bg-color)'
                    }, id='theme-light-container'),
                    
                    html.Div([
                        html.Img(
                            src='/static/assets/icons/lua.svg',
                            style={
                                'width': '30px',
                                'height': '30px',
                                'filter': 'var(--icon-filter)',
                                'cursor': 'pointer'
                            },
                            id='theme-dark-btn'
                        ),
                        html.P('Escuro', style={
                            'margin': '5px 0 0 0',
                            'fontSize': '12px',
                            'color': 'var(--primary-text-color)',
                            'textAlign': 'center'
                        })
                    ], style={
                        'display': 'flex',
                        'flexDirection': 'column',
                        'alignItems': 'center',
                        'padding': '10px',
                        'border': '2px solid transparent',
                        'borderRadius': '8px',
                        'margin': '0 5px',
                        'cursor': 'pointer',
                        'backgroundColor': 'var(--card-bg-color)'
                    }, id='theme-dark-container'),
                    
                    html.Div([
                        html.Img(
                            src='/static/assets/icons/contrast.png',
                            style={
                                'width': '30px',
                                'height': '30px',
                                'filter': 'var(--icon-filter)',
                                'cursor': 'pointer'
                            },
                            id='theme-contrast-btn'
                        ),
                        html.P('Alto Contraste', style={
                            'margin': '5px 0 0 0',
                            'fontSize': '12px',
                            'color': 'var(--primary-text-color)',
                            'textAlign': 'center'
                        })
                    ], style={
                        'display': 'flex',
                        'flexDirection': 'column',
                        'alignItems': 'center',
                        'padding': '10px',
                        'border': '2px solid transparent',
                        'borderRadius': '8px',
                        'margin': '0 5px',
                        'cursor': 'pointer',
                        'backgroundColor': 'var(--card-bg-color)'
                    }, id='theme-contrast-container'),
                    
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-around',
                    'alignItems': 'center'
                })
            ], className='theme-buttons-wrapper')
        ], className='config-item theme-selector-item'),

        dcc.Link(
            html.Div([
                html.Img(src='/static/assets/icons/about.png', className='icon-config',
                        style={"filter": "var(--icon-filter)"}),
                html.P("Sobre Nós", style={"color": "var(--primary-text-color)"}),
            ], className='config-item'),
            href='/dashboard/sobre-nos',
            style={'textDecoration': 'none', 'color': 'inherit'}
        ),

        html.A(
            html.Div([
                html.Img(src='/static/assets/icons/out.png', className='icon-config',
                        style={"filter": "var(--icon-filter)"}),
                html.P("Logout", style={"color": "var(--primary-text-color)"}),
            ], className='config-item'),
            href='/logout',
            style={'textDecoration': 'none', 'color': 'inherit', 'cursor': 'pointer'}
        ),

    ], className="config-list-container", style={"backgroundColor": "var(--card-bg-color)"}),

], id='page-content', className='page-content')

@callback(
    [Output('theme-mode', 'data'),
     Output('theme-light-container', 'style'),
     Output('theme-dark-container', 'style'),
     Output('theme-contrast-container', 'style')],
    [Input('theme-light-btn', 'n_clicks'),
     Input('theme-dark-btn', 'n_clicks'),
     Input('theme-contrast-btn', 'n_clicks')],
    [State('theme-mode', 'data')]
)
def update_theme_and_buttons(light_clicks, dark_clicks, contrast_clicks, current_theme):
    ctx = dash.callback_context
    if not ctx.triggered:
        light_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid transparent', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--card-bg-color)'}
        dark_style = light_style.copy()
        contrast_style = light_style.copy()
        
        if current_theme == 'light':
            light_style['border'] = '2px solid var(--accent-color)'
            light_style['backgroundColor'] = 'var(--accent-color)'
        elif current_theme == 'dark':
            dark_style['border'] = '2px solid var(--accent-color)'
            dark_style['backgroundColor'] = 'var(--accent-color)'
        elif current_theme == 'high-contrast':
            contrast_style['border'] = '2px solid var(--accent-color)'
            contrast_style['backgroundColor'] = 'var(--accent-color)'
            
        return current_theme, light_style, dark_style, contrast_style
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'theme-light-btn':
        new_theme = 'light'
        light_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid var(--accent-color)', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--accent-color)'}
        dark_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid transparent', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--card-bg-color)'}
        contrast_style = dark_style.copy()
    elif button_id == 'theme-dark-btn':
        new_theme = 'dark'
        dark_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid var(--accent-color)', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--accent-color)'}
        light_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid transparent', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--card-bg-color)'}
        contrast_style = light_style.copy()
    elif button_id == 'theme-contrast-btn':
        new_theme = 'high-contrast'
        contrast_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid var(--accent-color)', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--accent-color)'}
        light_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid transparent', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--card-bg-color)'}
        dark_style = light_style.copy()
    else:
        new_theme = current_theme
        light_style = {'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'padding': '10px', 'border': '2px solid transparent', 'borderRadius': '8px', 'margin': '0 5px', 'cursor': 'pointer', 'backgroundColor': 'var(--card-bg-color)'}
        dark_style = light_style.copy()
        contrast_style = light_style.copy()
    
    return new_theme, light_style, dark_style, contrast_style