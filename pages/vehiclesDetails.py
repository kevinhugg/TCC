import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime

from data.dados import viaturas, Ocur_Vehicles, agents

dash.register_page(__name__, path_template='/veiculo/<numero>', name=None)


def layout(numero=None):
    dados = next((v for v in viaturas if v['numero'] == numero), None)

    resp_veh = [a for a in agents if a['viatura_mes'] == numero]
    motorista = next((a for a in resp_veh if a['func_mes'].lower() == 'motorista'), None)
    another_agents = [a for a in resp_veh if a != motorista]

    if not (dados):
        return html.H3("Veículo não encontrado")

    meses_unicos = sorted(set(
        datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
        for o in Ocur_Vehicles if o['viatura'] == numero
    ))

    dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
        {
            'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(),
            'value': m
        } for m in meses_unicos
    ]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsVehicles.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),

        dcc.Store(id='vehicle-store', data=numero),

        html.Div([
            html.H3(f"Viatura - {dados['numero']}", className='tittle'),

            html.Div([
                html.Img(src=dados['imagem'], className='img'),
                html.Div([
                    html.P(f"Placa: {dados['placa']}", className='det placa'),
                    html.P(f"Tipo: {dados['veiculo']}", className='det tipo'),
                    html.P(f"Situação: {'Avariada' if dados['avariada'] else 'Operante'}",
                           className='det avariada' if dados['avariada'] else 'det operante'),
                    html.P(f"Local: {dados['loc_av'] if dados['avariada'] else ''}",
                           className='det loc_av'),
                ], className='texts-det'),
            ], className='details-items'),

            html.Div([
                html.Div([
                    html.A(id='rem_vehicle', children='Remover Veículo', className='btn rem_vehicle')
                ], className='btn_rem'),
            ], className='btn_rem_add'),

        ], className='details-container card'),

        html.Div([
            html.H4("Histórico de ocorrências da Viatura"),
            # colocar um icone para filtrar aqui por local da avaria, ocorrencia ou serviço
            dcc.Dropdown(
                id='filter-month',
                options=dropdown_options,
                value='todos',
                placeholder="Filtrar por mês...",
                className='filter-month'
            ),
            html.Div(id='table-ocurrences-vehicles'),
            html.Div([
                html.A(id='detalhes-pdf', children='Gerar PDF', target="_blank", className='btn-pdf')
            ], style={'margin-top': '2rem'}),
        ], className='ocurrences card'),

        html.Div([
            html.Div([
                html.H3(f"Responsáveis do Mês", className='tittle'),
                dcc.Dropdown(
                    id='dropdown-turnos',
                    options=[
                        {'label': 'Manhã', 'value': 'manha'},
                        {'label': 'Tarde', 'value': 'tarde'},
                        {'label': 'Noite', 'value': 'noite'},
                    ],
                    placeholder='Selecione um turno',
                    className='dropdown-turnos',
                    style={'height': '40px', 'width': '200px'}
                ),
            ], className='dropdown-title'),

            html.Div([
                html.Div([
                    html.Img(src=motorista['foto_agnt'], className='img_agent'),
                    html.P(f"{motorista['nome']}", className='agent-name'),
                    html.P(f"Função: {motorista['func_mes'].capitalize()}", className='agent-role'),
                    html.P(f"{motorista['cargo_at']}", className='agent-cargo'),
                ], className='agent-box motorista') if motorista else html.Div(
                    html.Div([
                        html.P("Sem motorista", className='agent-name'),
                    ], className='add-driver-box-content'),
                    id='add-driver-button', className='agent-box add-driver-box', title='Adicionar motorista'
                ),
                *[
                    dcc.Link(
                        html.Div([
                            html.Img(src=agente['foto_agnt'], className='img_agent'),
                            html.P(f"{agente['nome']}", className='agent-name'),
                            html.P(f"Função: {agente['func_mes'].capitalize()}", className='agent-role'),
                            html.P(f"{agente['cargo_at']}", className='agent-cargo'),
                            html.P("Turno não iniciado", className='turno-status'),
                        ], className='agent-box'),
                        href=f"/dashboard/agent/{agente['id']}", className='link-ag-vt'
                    ) for agente in another_agents
                ],

                html.Div(
                    html.Div(
                        html.H1("+", className='add-agent-icon'),
                        id='add-agent-button', className='agent-box add-agent-box', title='Adicionar agente'),
                )
            ], className='agents-grid'),

        ], className='agents-container card'),

        html.Div(
            id='agent-modal',
            className='modal',
            style={'display': 'none'},
            children=[
                html.Div(
                    className='modal-content',
                    children=[
                        html.Div(className='modal-header', children=[
                            html.H2('Adicionar Agente'),
                            html.Span(id='modal-close-button', className='modal-close-button', children='×'),
                        ]),
                        html.Div(className='modal-body', children=[
                            dcc.Dropdown(
                                id='agent-filter-dropdown',
                                options=[
                                    {'label': 'Todos os Agentes', 'value': 'all'},
                                    {'label': 'Agentes Sem Função', 'value': 'unassigned'},
                                ],
                                value='all',
                                clearable=False
                            ),
                            dcc.RadioItems(id='agent-list', value=None),
                        ]),
                        html.Div(className='modal-footer', children=[
                            html.Button('Atribuir Agente', id='assign-agent-button', className='btn')
                        ]),
                    ]
                )
            ]
        ),

    ], className='page-content'),

@callback(
    Output('table-ocurrences-vehicles', 'children'),
    Input('filter-month', 'value'),
    Input('vehicle-store', 'data')
)
def att_tabela_oco(mes, viatura):
    ocorrencias = [o for o in Ocur_Vehicles if o['viatura'] == viatura and o.get('class') == 'ocorrencia']

    if mes != 'todos':
        ocorrencias = [
            o for o in ocorrencias
            if datetime.strptime(o['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]

    if not ocorrencias:
        return html.P("Nenhuma ocorrência registrada para este período.")

    return html.Table([
        html.Thead(
            html.Tr([
                html.Th("Data"),
                html.Th("Tipo"),
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(o['data']),
                html.Td(o['nomenclatura']),
                dcc.Link(
                    html.Td('Ver Mais', className='bt'),
                    href=f"/dashboard/ocurrences/{o['id']}",
                    className="btn_view"
                )
            ])
            for o in ocorrencias
        ])
    ], className='table-ocurrences')


@callback(
    Output('detalhes-pdf', 'href'),
    Input('filter-month', 'value'),
    Input('vehicle-store', 'data')
)
def atualizar_link_pdf(filtro_status, numero):
    return f"/pdf_detalhes_viatura_{numero}?status={filtro_status}"


@callback(
    Output('agent-modal', 'style'),
    Input('add-driver-button', 'n_clicks'),
    Input('add-agent-button', 'n_clicks'),
    Input('modal-close-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_modal(add_driver_clicks, add_agent_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id in ['add-driver-button', 'add-agent-button']:
        return {'display': 'block'}

    if trigger_id == 'modal-close-button':
        return {'display': 'none'}

    return {'display': 'none'}


@callback(
    Output('agent-list', 'options'),
    Input('agent-filter-dropdown', 'value')
)
def update_agent_list(filter_value):
    if filter_value == 'unassigned':
        filtered_agents = [a for a in agents if not a.get('func_mes') or a.get('func_mes').lower() == '']
    else:
        filtered_agents = agents

    return [{'label': f"{a['nome']} ({a['cargo_at']})", 'value': a['id']} for a in filtered_agents]


@callback(
    Output('agent-modal', 'style', allow_duplicate=True),
    Input('assign-agent-button', 'n_clicks'),
    State('agent-list', 'value'),
    State('vehicle-store', 'data'),
    prevent_initial_call=True
)
def assign_agent(n_clicks, agent_id, vehicle_numero):
    if n_clicks and agent_id and vehicle_numero:
        print(f"Assigning agent {agent_id} to vehicle {vehicle_numero}")
        return {'display': 'none'}
    return dash.no_update