import dash
from dash import Dash, html, dcc, Input, Output, callback, ctx
import dash_bootstrap_components as dbc
from flask import session
import firebase_functions as fb  
import urllib.parse
from sidebar import get_sidebar

def create_dash_app(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dashboard/',
        use_pages=True,
        external_stylesheets=[
            '/static/css/global.css',
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
        ],
        suppress_callback_exceptions=True,
    )

    dash_app.layout = html.Div([
        dcc.Location(id='url', refresh=True),
        dcc.Store(id='theme-mode', storage_type='local'),
        dcc.Store(id='user-profile-image', data={'profile_image': '/static/assets/img/persona.png'}),
        dcc.Store(id='user-auth-store', data=''),

        html.Div(id='theme', children=[
            html.Div([
                dcc.Link(
                    html.Img(
                        id='header-profile-pic', 
                        src='/static/assets/img/persona.png', 
                        className='profile-pic'
                    ),
                    href='/dashboard/profile'
                )
            ], className='header'),

            html.Div(get_sidebar(), className='sidebar'),

            html.Div(dash.page_container, id='page-content', className='page-content')
        ])
    ], id='body', className='parent')

    @dash_app.callback(
        Output('header-profile-pic', 'src'),
        [Input('url', 'pathname'),
         Input('user-auth-store', 'data'),
         Input('user-profile-image', 'data')],
        prevent_initial_call=True
    )
    def load_header_profile_pic(pathname, auth_data, profile_image_data):
        try:
            if profile_image_data and 'profile_image' in profile_image_data:
                new_image = profile_image_data['profile_image']
                if new_image and new_image != '/static/assets/img/persona.png':
                    return new_image
            
            user_id = session.get('user_id')
            
            if not user_id:
                return '/static/assets/img/persona.png'
            
            adms = fb.get_all_adms()
            
            current_user = None
            user_type = None
            
            for adm in adms:
                adm_uid = adm.get('uid')
                if adm_uid == user_id:
                    current_user = adm
                    user_type = 'adm'
                    break
            
            if not current_user:
                agents = fb.get_all_agents()
                
                for agent in agents:
                    agent_uid = agent.get('uid')
                    if agent_uid == user_id:
                        current_user = agent
                        user_type = 'agent'
                        break
            
            if not current_user:
                return '/static/assets/img/persona.png'
            
            if user_type == 'adm':
                foto_path = current_user.get('foto_agnt', '')
            else:
                foto_path = current_user.get('foto_agnt', '')
            
            if not foto_path or foto_path == '/static/assets/img/persona.png':
                return '/static/assets/img/persona.png'
            
            if foto_path.startswith('http'):
                return foto_path
            
            if 'agentes/' in foto_path or 'adms/' in foto_path:
                if user_type == 'adm' and 'adms/' in foto_path:
                    folder = 'adms'
                    filename = foto_path.replace('adms/', '')
                else:
                    folder = 'agentes'
                    filename = foto_path.replace('agentes/', '')
                
                encoded_filename = urllib.parse.quote(filename, safe='')
                firebase_url = f"https://firebasestorage.googleapis.com/v0/b/tcc-semurb-2ea61.appspot.com/o/{folder}%2F{encoded_filename}?alt=media"
                return firebase_url
            
            return '/static/assets/img/persona.png'
            
        except Exception as e:
            return '/static/assets/img/persona.png'

    @dash_app.callback(
        Output('header-profile-pic', 'src', allow_duplicate=True),
        Input('user-profile-image', 'data'),
        prevent_initial_call=True
    )
    def update_header_from_store(profile_image_data):
        if profile_image_data and 'profile_image' in profile_image_data:
            new_image = profile_image_data['profile_image']
            return new_image
        return dash.no_update

    @callback(
        [Output('theme', 'className'),
         Output('body', 'className')],
        Input('theme-mode', 'data'),
        prevent_initial_call=False
    )
    def update_theme(mode):
        if mode == 'dark':
            return 'dark-mode', 'dark-mode'
        elif mode == 'high-contrast':
            return 'high-contrast-mode', 'high-contrast-mode'
        else:
            return 'light-mode', 'light-mode'

    return dash_app