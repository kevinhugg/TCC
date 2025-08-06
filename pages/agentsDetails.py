import dash
from dash import html, dcc, Input, Output, callback
from datetime import datetime

from data.dados import viaturas, Ocur_Vehicles, agents

dash.register_page(__name__, path_template='/agent/<id>', name=None)

def layout(id=None):
    dados = next((a for a in agents if a['id'] == id), None)

    if not(dados):
        return html.H3("Agente não encontrado")

    numero = dados ['viatura_mes']
    dates = next((v for v in viaturas if v['numero'] == numero), None)
    resp_veh = [a for a in agents if a['viatura_mes'] == numero]
    motorista = next((a for a in resp_veh if a.get('func_mes', '').lower() == 'motorista'), None)
    another_agents = [a for a in resp_veh if motorista is None or a['id'] != motorista['id']]

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

        dcc.Store(id='agent-store', data=id),

        html.Div([
            html.H3(f"Agente - {dados['nome']}", className='tittle'),

            html.Div([
                html.Img(src=dados['foto_agnt'], className='img_agent'),
                html.Div([
                    html.P(f"Cargo: {dados['cargo_at']}", className='det carg'),
                    html.P(f"Funcão(Mês): {dados['func_mes']}", className='det func'),
                    dcc.Link(
                        html.P(f"Viatura(Mês): {dados['viatura_mes']}", className='det viat'),
                        href=f"/dashboard/veiculo/{dates['numero']}" if dates else '#',
                        className='link-ag-vt'
                    )
                ], className='texts-det'),
            ], className='details-items'),

            html.Div([
                html.Div([
                    html.A(id='rem_agent', children='Remover Agente', className='btn rem_vehicle')
                ], className='btn_rem'),
            ], className='btn_rem_add'),

        ], className='details-container card'),

        html.Div([
            html.H4("Histórico do Agente"),
            dcc.Dropdown(
                id='filter-month',
                options=dropdown_options,
                value='todos',
                placeholder="Filtrar por mês...",
                className='filter-month'
            ),
            html.Div(id='table-ocurrences-agents'),
            html.Div([
                html.A(id='detalhes-agente-pdf', children='Gerar PDF', target="_blank", className='btn-pdf')
            ], style={'margin-bottom': '2rem'}),
        ], className='ocurrences card'),

        html.Div([
            html.H3(f"Equipe do Mês", className='tittle'),

            html.Div([
                *(
                    [
                        dcc.Link(
                            html.Div([
                                html.Img(
                                    src=motorista['foto_agnt'] if motorista and motorista.get(
                                        'foto_agnt') else '/static/img/default-user.png',
                                    className='img'
                                ),
                                html.P(motorista['nome'], className='agent-name'),
                                html.P(f"Função: {motorista['func_mes'].capitalize()}", className='agent-role'),
                                html.P(motorista['cargo_at'], className='agent-cargo'),
                            ], className='agent-box motorista'),
                            href=f"/dashboard/agent/{motorista['id']}", className='link-ag-vt')
                    ] if motorista else []
                ),

                *[
                    dcc.Link(
                        html.Div([
                            html.Img(
                                src=agente.get('foto_agnt') or '/static/img/default-user.png',
                                className='img'
                            ),
                            html.P(agente.get('nome', 'Nome não informado'), className='agent-name'),
                            html.P(f"Função: {agente.get('func_mes', 'Não definido').capitalize()}", className='agent-role'),
                            html.P(agente.get('cargo_at', ''), className='agent-cargo'),
                        ], className='agent-box'),
                        href=f"/dashboard/agent/{agente['id']}", className='link-ag-vt'
                    ) for agente in another_agents

                ]
            ], className='agents-grid'),


        ], className='agents-container card'),

    ], className='page-content')


@callback(
    Output('table-ocurrences-agents', 'children'),
    Input('filter-month', 'value'),
    Input('agent-store', 'data')
)
def att_tabela_oco_agents(mes, agent_id):

    agente = next((a for a in agents if a['id'] == agent_id), None)
    if not agente:
        return html.P("Agente não encontrado.")

    numero_viatura = agente.get('viatura_mes')

    ocurrences_veh = [o for o in Ocur_Vehicles if o['viatura'] == numero_viatura]

    if mes != 'todos':
        ocurrences_veh = [
            o for o in ocurrences_veh
            if datetime.strptime(o['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]

    if not ocurrences_veh:
        return html.P("Nenhuma ocorrência registrada para este período.")

    return html.Table([
        html.Thead(
            html.Tr([
                html.Th("Data"),
                html.Th("Descrição")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(o['data']),
                html.Td(o['descricao'])
            ]) for o in ocurrences_veh
        ])
    ], className='table-ocurrences')

@callback(
    Output('detalhes-agente-pdf', 'href'),
    Input('filter-month', 'value'),
    Input('agent-store', 'data')
)
def atualizar_agentes_detalhes_pdf(filtro_status, agente_id):
    return f"/gerar_pdf_agentes_ocorrencias?filtro={agente_id}&status={filtro_status}"