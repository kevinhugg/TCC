import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime
from data.dados import Ocur_Vehicles, viaturas, agents

dash.register_page(__name__, path_template='/ocurrences/<id>', name=None)

def layout(id=None):
    # Find the occurrence by ID from the local data
    dados = next((item for item in Ocur_Vehicles if item.get('id') == id), None)

    if not dados or dados.get('class') != 'ocorrencia':
        return html.Div([
            html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
            html.Div([
                html.Div("Ocorrência não encontrada ou inválida.", style={'textAlign': 'center', 'fontSize': '20px'}),
                html.Br(),
                html.A("Voltar para Ocorrências", href="/dashboard/ocurrences", className="btn btn-primary")
            ], style={'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '30px', 'boxShadow': '0 0 10px rgba(0,0,0,0.25)', 'textAlign': 'center', 'zIndex': 9999})
        ])

    vehicle_number = dados.get('viatura')
    # Find vehicle data from local viaturas list
    vehicle_data = next((v for v in viaturas if v.get('numero') == vehicle_number), None)
    # Find team agents from local agents list
    team_agents = [a for a in agents if a.get('viatura_mes') == vehicle_number]
    # Note: 'funcao' in dados.py is 'func_mes'
    motorista = next((a for a in team_agents if a.get('func_mes', '').lower() == 'motorista'), None)
    another_agents = [a for a in team_agents if a != motorista]

    # Get history for the vehicle from local data
    history = [h for h in Ocur_Vehicles if h.get('viatura') == vehicle_number]
    meses_unicos = sorted(list(set(datetime.strptime(h['data'], "%Y-%m-%d").strftime("%Y/%m") for h in history if h.get('class') == 'ocorrencia')))
    dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
        {'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(), 'value': m} for m in meses_unicos
    ]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='oc-store', data=id),
        dcc.Location(id='redirect-oco', refresh=True),

        # Deletion Modal
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
            html.H3(f"{dados.get('nomenclatura', 'N/A')}", className='tittle'),
            html.Div([
                html.Div([
                    html.P(f"Descrição: {dados.get('descricao', 'Não informada.')}"),
                    html.P(f"Endereço: {dados.get('endereco', 'Não informado.')}"),
                    html.P(f"Cidadão atendido: {dados.get('n_cidadao', 'Não informado.')}"),
                    html.P(f"Contato do cidadão: {dados.get('contato', 'Não informado.')}"),
                    dcc.Link(
                        html.P(f"Veículo: {dados.get('viatura', 'N/A')}"),
                        href=f"/dashboard/veiculo/{vehicle_data.get('numero')}" if vehicle_data else '#',
                        className='link-ag-vt'
                    )
                ], className='texts-det'),
            ], className='details-items'),
            html.Div([
                html.Div([
                    html.A(id='del_oco', children='Remover Ocorrência', className='btn rem_vehicle')
                ], className='btn_rem'),
                html.Div([
                    html.A(id='pdf_oco_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf'),
            ], className='btn_rem_pdf'),
        ], className='details-container'),

        html.Div([
            html.Div([
                html.H3(f"Responsáveis do Mês", className='tittle'),
                dcc.Dropdown(
                    id='dropdown-turnos-oco',
                    options=[
                        {'label': 'Todos os Turnos', 'value': 'todos'},
                        {'label': 'Manhã', 'value': 'manha'},
                        {'label': 'Tarde', 'value': 'tarde'},
                        {'label': 'Noite', 'value': 'noite'},
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

    # Find the occurrence by ID from the local data
    occurrence_data = next((item for item in Ocur_Vehicles if item.get('id') == occurrence_id), None)
    if not occurrence_data:
        return []

    vehicle_number = occurrence_data.get('viatura')
    # Find team agents from local agents list
    all_agents_for_vehicle = [a for a in agents if a.get('viatura_mes') == vehicle_number]

    # 2. Filtra por turno
    if selected_shift and selected_shift != 'todos':
        agents_to_display = [a for a in all_agents_for_vehicle if a.get('turno') == selected_shift]
    else:
        agents_to_display = all_agents_for_vehicle

    # 3. Separa motorista e outros agentes
    motorista = next((a for a in agents_to_display if a.get('func_mes', '').lower() == 'motorista'), None)
    another_agents = [a for a in agents_to_display if a != motorista]

    # 4. Cria os componentes HTML
    children = []

    # Box do Motorista
    if motorista:
        children.append(
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=motorista.get('foto_agnt'), className='img_agent'),
                        html.P(f"{motorista.get('nome')}", className='agent-name'),
                        html.P(f"Função: {motorista.get('func_mes', '').capitalize()}", className='agent-role'),
                        html.P(f"Turno: {motorista.get('turno', 'N/A').capitalize()}", className='turno-status'),
                    ], className='agent-box-link'),
                    href=f"/dashboard/agent/{motorista.get('id')}", className='link-ag-vt'
                )
            ], className='agent-box motorista')
        )
    else:
        children.append(
            html.Div(
                html.Div([
                    html.P("Sem motorista para este turno", className='agent-name'),
                ], className='add-driver-box-content'),
                id='add-driver-button', className='agent-box add-driver-box', title='Adicionar motorista',
                style={'display': 'none' if motorista else 'block'}
            )
        )

    # Boxes dos outros agentes
    for agente in another_agents:
        children.append(
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=agente.get('foto_agnt'), className='img_agent'),
                        html.P(f"{agente.get('nome')}", className='agent-name'),
                        html.P(f"Função: {agente.get('func_mes', '').capitalize()}", className='agent-role'),
                        html.P(f"Turno: {agente.get('turno', 'N/A').capitalize()}", className='turno-status'),
                    ], className='agent-box-link'),
                    href=f"/dashboard/agent/{agente.get('id')}", className='link-ag-vt'
                )
            ], className='agent-box')
        )
    return children