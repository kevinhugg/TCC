import dash
from dash import html, dcc
from data.dados import agents

dash.register_page(__name__, path='/profile', name='Profile')

def layout():
    # Assuming the logged-in agent is the first one in the list for this example
    agent_data = agents[0] if agents else {}

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/profile.css'),
        html.Div([
            html.Img(src=agent_data.get('foto_agnt', '/static/assets/img/persona.png'), className='profile-img'),
            html.H3(agent_data.get('nome', 'Nome do Agente'), className='profile-name'),
            html.P(f"Cargo: {agent_data.get('cargo', 'N/A')}", className='profile-info'),
            html.P(f"Função: {agent_data.get('func_mes', 'N/A')}", className='profile-info'),
            html.P(f"Turno: {agent_data.get('turno', 'N/A')}", className='profile-info'),
            html.P(f"Viatura: {agent_data.get('viatura_mes', 'N/A')}", className='profile-info'),
        ], className='profile-container card'),
    ], className='page-content profile-page')