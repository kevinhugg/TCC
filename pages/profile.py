import dash
from dash import html
from data.dados import adm

dash.register_page(__name__, path='/profile', name='Perfil', className='pg-at')

layout = html.Div([
    html.Link(rel='stylesheet', href='/static/css/profile.css'),
    html.Div([
        html.Div([
            html.Img(src='static/assets/img/persona.png', className='profile-pic-large'),
            html.H3(adm['nome'], className='profile-name-large'),
            html.P(f"Email: {adm['email']}", className='profile-detail'),
            html.P(f"Cargo: {adm['cargo']}", className='profile-detail'),
            html.P(f"Idade: {adm['idade']}", className='profile-detail'),
        ], className='profile-container')
    ], className='page-content')
])
