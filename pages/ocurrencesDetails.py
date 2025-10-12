import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime
import sys
import os
import urllib.parse

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from firebase_functions import get_occurrence_by_id, get_all_agents, get_all_vehicles, get_agents_by_vehicle, delete_occurrence
    FIREBASE_AVAILABLE = True
except ImportError as e:
    FIREBASE_AVAILABLE = False

dash.register_page(__name__, path_template='/ocurrences/<occurrence_id>', name='Detalhes da Ocorrência')

def layout(occurrence_id=None):
    if occurrence_id:
        try:
            decoded_id = urllib.parse.unquote(occurrence_id)
            occurrence_id = decoded_id
        except Exception as e:
            pass
    
    if FIREBASE_AVAILABLE and occurrence_id:
        dados = get_occurrence_by_id(occurrence_id)
    else:
        dados = None

    if not dados:
        return html.Div([
            html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
            html.Div([
                html.Div([
                    html.H3("Ocorrência Não Encontrada", style={'color': 'red'}),
                    html.P(f"ID: {occurrence_id}"),
                    html.P("A ocorrência solicitada não foi encontrada no sistema."),
                    html.P("Isso pode acontecer se:"),
                    html.Ul([
                        html.Li("A ocorrência foi excluída"),
                        html.Li("O ID está incorreto"),
                        html.Li("Houve um problema de conexão")
                    ]),
                    html.Br(),
                    dcc.Link(
                        "Voltar para Ocorrências", 
                        href="/dashboard/ocurrences",
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

    motorista = next((a for a in team_agents if a.get('funcao', '').lower() == 'motorista'), None)
    another_agents = [a for a in team_agents if a != motorista]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='oc-store', data=occurrence_id),
        dcc.Location(id='redirect-oco', refresh=True),

        html.Div(id='delete-modal-oco', className='modal', style={'display': 'none'}, children=[
            html.Div(className='modal-content', children=[
                html.Div(className='modal-header', children=[
                    html.H5('Confirmar Exclusão'),
                    html.Button('×', id='close-modal-oco', className='modal-close-button')
                ]),
                html.Div(className='modal-body', children=[
                    html.P("Você tem certeza que deseja excluir esta ocorrência?")
                ]),
                html.Div(className='modal-footer', children=[
                    html.Button('Cancelar', id='cancel-delete-oco', className='btn btn-secondary'),
                    html.Button('Excluir', id='confirm-delete-oco', className='btn btn-danger')
                ])
            ])
        ]),

        html.Div([
            html.H3(f"{dados.get('nomenclatura', dados.get('tipo_ocorrencia', 'Ocorrência'))}", className='tittle'),
            html.Div([
                html.Div([
                    html.P(f"Data: {dados.get('data', 'N/A')} {dados.get('horario', '')}"),
                    html.P(f"Tipo: {dados.get('tipo_ocorrencia', dados.get('tipo', 'N/A'))}"),
                    html.P(f"Descrição: {dados.get('descricao', 'Não informada.')}"),
                    html.P(f"Endereço: {dados.get('endereco', 'Não informado.')}"),
                    html.P(f"Cidadão atendido: {dados.get('nome', dados.get('n_cidadao', 'Não informado.'))}"),
                    html.P(f"Contato: {dados.get('contato', dados.get('numcontato', 'Não informado.'))}"),
                    html.P(f"Responsável: {dados.get('responsavel', 'N/A')}"),
                    dcc.Link(
                        html.P(f"Veículo: {dados.get('viatura', 'N/A')}"),
                        href=f"/veiculo/{vehicle_number}" if vehicle_number else '#',
                        className='link-ag-vt'
                    )
                ], className='texts-det'),
            ], className='details-items'),
            
            html.Div([
                html.Img(
                    src=dados.get('fotoUrl', ''),
                    style={'maxWidth': '100%', 'maxHeight': '300px', 'display': 'block' if dados.get('fotoUrl') else 'none'}
                ) if dados.get('fotoUrl') else html.Div()
            ], className='occurrence-photo', style={'textAlign': 'center', 'margin': '20px 0'}),
            
            html.Div([
                html.Div([
                    html.A(id='pdf_oco_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf'),
                    html.Button('Excluir Ocorrência', id='delete-oco-btn', className='btn btn-danger', style={'marginLeft': '10px'})
                ], className='btn-pdf'),
            ], className='btn_rem_pdf'),
        ], className='details-container'),

        html.Div([
            html.Div([
                html.H3(f"Responsáveis do Veículo", className='tittle'),
                dcc.Dropdown(
                    id='dropdown-turnos-oco',
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

            html.Div(id='agents-grid-oco', className='agents-grid'),

        ], className='agents-container card'),

    ], className='page-content details-page')

@callback(
    Output('agents-grid-oco', 'children'),
    Input('dropdown-turnos-oco', 'value'),
    State('oc-store', 'data')
)
def update_agents_by_shift_oco(selected_shift, occurrence_id):
    if not occurrence_id:
        return []

    if FIREBASE_AVAILABLE:
        occurrence_data = get_occurrence_by_id(occurrence_id)
        if not occurrence_data:
            return []
        
        vehicle_number = occurrence_data.get('viatura')
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
                    href=f"/agent/{motorista.get('id')}", 
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
                    href=f"/agent/{agente.get('id')}", 
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
    Output('delete-modal-oco', 'style'),
    [Input('delete-oco-btn', 'n_clicks'),
     Input('close-modal-oco', 'n_clicks'),
     Input('cancel-delete-oco', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, close_clicks, cancel_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'delete-oco-btn':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@callback(
    Output('pdf_oco_serv_det_gerar', 'href'),
    Input('oc-store', 'data'),
    prevent_initial_call=False 
)
def generate_pdf_link(occurrence_id):
    if occurrence_id:
        encoded_id = urllib.parse.quote(occurrence_id, safe='')
        pdf_link = f"/gerar_pdf_ocorrencia_detalhes?id={encoded_id}"
        return pdf_link
    
    return ""

@callback(
    Output('redirect-oco', 'pathname'),
    Input('confirm-delete-oco', 'n_clicks'),
    State('oc-store', 'data'),
    prevent_initial_call=True
)
def confirm_delete_occurrence(n_clicks, occurrence_id):
    if n_clicks and occurrence_id:
        if FIREBASE_AVAILABLE:
            occurrence_data = get_occurrence_by_id(occurrence_id)
            if occurrence_data:
                agent_id = occurrence_data.get('responsavel_id')
                date = occurrence_data.get('data')
                
                if agent_id and date:
                    success = delete_occurrence(agent_id, date, occurrence_id)
                    if success:
                        return '/dashboard/ocurrences'
        
        return '/dashboard/ocurrences'
    
    return dash.no_update