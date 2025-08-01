import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from sidebar import get_sidebar

def create_dash_app(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dashboard/',
        use_pages=True,
        external_stylesheets=[dbc.themes.DARKLY],
    )

    dash_app.layout = html.Div([

        dcc.Location(id='url', refresh=True),
        dcc.Store(id='theme-mode', storage_type='local'),

        html.Div(id='theme', children=[
            # Header fixo no topo
            html.Div([
                html.Img(src='/static/assets/img/persona.png', className='profile-pic')
            ], className='header'),

            # Sidebar
            html.Div(get_sidebar(), className='sidebar'),

            # Conteúdo da página
            html.Div(dash.page_container, id='page-content', className='page-content')

        ])

    ], className='parent')

    return dash_app