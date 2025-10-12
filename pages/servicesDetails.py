import dash
from dash import html, dcc, Input, Output, callback, State
import sys
import os
import urllib.parse

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from firebase_functions import get_service_by_id, get_all_vehicles, get_agents_by_vehicle
    FIREBASE_AVAILABLE = True
except ImportError as e:
    FIREBASE_AVAILABLE = False

dash.register_page(__name__, path_template='/services/<id>', name='Detalhes do Serviço')

def layout(id=None):
    if id:
        try:
            decoded_id = urllib.parse.unquote(id)
            id = decoded_id
        except Exception:
            pass
    
    if FIREBASE_AVAILABLE and id:
        dados = get_service_by_id(id)
    else:
        dados = None

    if not dados:
        return html.Div([
            html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
            html.Div([
                html.Div([
                    html.H3("Serviço Não Encontrado", style={'color': 'red'}),
                    html.P(f"ID: {id}"),
                    html.P("O serviço solicitado não foi encontrado no sistema."),
                    html.P("Isso pode acontecer se:"),
                    html.Ul([
                        html.Li("O serviço foi excluído"),
                        html.Li("O ID está incorreto"),
                        html.Li("Houve um problema de conexão")
                    ]),
                    html.Br(),
                    dcc.Link(
                        "Voltar para Serviços", 
                        href="/dashboard/services",
                        style={
                            'textDecoration': 'none',
                            'color': 'white',
                            'padding': '10px 20px',
                            'backgroundColor': '#007bff',
                            'borderRadius': '4px',
                            'display': 'inline-block'
                        }
                    )
                ])
            ], style={'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '30px', 'boxShadow': '0 0 10px rgba(0,0,0,0.25)', 'textAlign': 'center', 'zIndex': 9999})
        ])

    vehicle_number = dados.get('viatura')
    
    if FIREBASE_AVAILABLE:
        all_vehicles = get_all_vehicles()
        vehicle_data = next((v for v in all_vehicles if v.get('numero') == vehicle_number), None)
        team_agents = get_agents_by_vehicle(vehicle_number)
    else:
        vehicle_data = None
        team_agents = []

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='serv-store', data=id),
        dcc.Location(id='redirect-serv', refresh=True),

        html.Div([
            html.Div([
                html.H3(f"{dados.get('nomenclatura', 'Serviço de Viário')}", className='tittle'),
                html.Div([
                    html.Div([
                        html.P(f"Data: {dados.get('data', 'N/A')} {dados.get('horario', '')}"),
                        html.P(f"Tipo: {dados.get('tipo', 'Serviço Viário')}"),
                        html.P(f"Descrição: {dados.get('descricao', 'Não informada.')}"),
                        html.P(f"Endereço: {dados.get('endereco', 'Não informado.')}"),
                        html.P(f"Local: {dados.get('local', 'Não informado.')}"),
                        html.P(f"Observações: {dados.get('observacoes', 'Não informadas.')}"),
                        html.P(f"Quantidade de Itens: {dados.get('qtd_items', 'N/A')}"),
                        html.P(f"Responsável: {dados.get('responsavel', 'N/A')}"),
                        dcc.Link(
                            html.P(f"Veículo: {dados.get('viatura', 'N/A')}"),
                            href=f"/dashboard/veiculo/{vehicle_number}" if vehicle_number else '#',
                            className='link-ag-vt'
                        )
                    ], className='texts-det'),
                ], className='details-items'),
                
                html.Div([
                    html.Img(
                        src=dados.get('fotoUrl', ''),
                        style={'maxWidth': '100%', 'maxHeight': '300px', 'display': 'block' if dados.get('fotoUrl') else 'none'}
                    ) if dados.get('fotoUrl') else html.Div()
                ], className='service-photo', style={'textAlign': 'center', 'margin': '20px 0'}),
                
                html.Div([
                    html.Div([
                        html.A(id='pdf_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf'),
                    ], className='btn-pdf'),
                ], className='btn_pdf'),
            ], className='details-container card'),
        ], className='details-section', style={'marginBottom': '30px'}),

        html.Div([
            html.Div([
                html.Div([
                    html.H3(f"Responsáveis do Veículo", className='tittle'),
                    dcc.Dropdown(
                        id='dropdown-turnos-serv',
                        options=[
                            {'label': 'Todos os turnos', 'value': 'todos'},
                            {'label': 'Manhã', 'value': 'manha'},
                            {'label': 'Tarde', 'value': 'tarde'},
                            {'label': 'Noite', 'value': 'noite'}
                        ],
                        value='todos',
                        clearable=False,
                        className='dropdown-turnos',
                        style={'height': '40px', 'width': '200px'}
                    ),
                ], className='dropdown-title'),

                html.Div(id='agents-grid-serv', className='agents-grid'),

            ], className='agents-container card'),
        ], className='agents-section'),

    ], className='page-content details-page vertical-layout')

@callback(
    Output('agents-grid-serv', 'children'),
    Input('dropdown-turnos-serv', 'value'),
    State('serv-store', 'data')
)
def update_agents_by_shift_serv(selected_shift, service_id):
    if not service_id:
        return []

    if FIREBASE_AVAILABLE:
        service_data = get_service_by_id(service_id)
        if not service_data:
            return []
        
        vehicle_number = service_data.get('viatura')
        all_agents_for_vehicle = get_agents_by_vehicle(vehicle_number)
    else:
        return []

    if selected_shift and selected_shift != 'todos':
        agents_to_display = [a for a in all_agents_for_vehicle if a.get('turno', '').lower() == selected_shift]
    else:
        agents_to_display = all_agents_for_vehicle

    motorista = next((a for a in agents_to_display if a.get('funcao', '').lower() == 'motorista'), None)
    another_agents = [a for a in agents_to_display if a != motorista]

    children = []

    if motorista:
        children.append(
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(
                            src=motorista.get('foto_agnt', '/static/images/default_agent.jpg'), 
                            className='img_agent',
                            onError="this.src='/static/images/default_agent.jpg'"
                        ),
                        html.P(f"{motorista.get('nome', 'N/A')}", className='agent-name'),
                        html.P(f"Função: {motorista.get('funcao', '').capitalize()}", className='agent-role'),
                        html.P(f"Turno: {motorista.get('turno', 'N/A').capitalize()}", className='turno-status'),
                    ], className='agent-box-link'),
                    href=f"/dashboard/agent/{motorista.get('id')}", 
                    className='link-ag-vt'
                )
            ], className='agent-box motorista')
        )
    else:
        children.append(
            html.Div(
                html.Div([
                    html.P("Sem motorista para este turno", className='agent-name'),
                ], className='add-driver-box-content'),
                className='agent-box add-driver-box', 
                title='Adicionar motorista',
                style={'display': 'block'}
            )
        )

    for agente in another_agents:
        children.append(
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(
                            src=agente.get('foto_agnt', '/static/images/default_agent.jpg'), 
                            className='img_agent',
                            onError="this.src='/static/images/default_agent.jpg'"
                        ),
                        html.P(f"{agente.get('nome', 'N/A')}", className='agent-name'),
                        html.P(f"Função: {agente.get('funcao', '').capitalize()}", className='agent-role'),
                        html.P(f"Turno: {agente.get('turno', 'N/A').capitalize()}", className='turno-status'),
                    ], className='agent-box-link'),
                    href=f"/dashboard/agent/{agente.get('id')}", 
                    className='link-ag-vt'
                )
            ], className='agent-box')
        )
    
    if not agents_to_display:
        children.append(
            html.Div([
                html.P("Nenhum agente encontrado para este veículo/turno.", className='agent-name')
            ], className='agent-box', style={'textAlign': 'center'})
        )
    
    return children

@callback(
    Output('pdf_serv_det_gerar', 'href'),
    Input('serv-store', 'data')
)
def generate_pdf_link(service_id):
    if service_id:
        encoded_id = urllib.parse.quote(service_id, safe='')
        pdf_link = f"/gerar_pdf_servico_detalhes?id={encoded_id}"
        return pdf_link
    
    return ""

@callback(
    Output('redirect-serv', 'pathname'),
    Input('serv-store', 'data')
)
def handle_redirect(service_id):
    return dash.no_update