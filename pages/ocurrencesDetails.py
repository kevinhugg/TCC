import dash
from dash import html, dcc, Input, Output, callback
from datetime import datetime

from data.dados import agents, Ocur_Vehicles, viaturas

dash.register_page(__name__, path_template='/ocurrences/<id>', name=None)

def layout(id=None):
    dados = next((o for o in Ocur_Vehicles if o['id'] == id and o.get('class') == 'ocorrencia'), None)

    if not dados:
        return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),

            dcc.Location(id='n_oco_popup', refresh=True),
            html.Div([
                html.Div("Essa não é uma ocorrência.", style={
                    'fontSize': '20px',
                    'marginBottom': '15px'
                }),
                html.Button("Voltar", id="botao-voltar", style={
                    'backgroundColor': '#007BFF',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'cursor': 'pointer',
                    'borderRadius': '5px',
                    'fontSize': '16px'
                })
            ], style={
                'position': 'fixed',
                'top': '50%',
                'left': '50%',
                'transform': 'translate(-50%, -50%)',
                'backgroundColor': 'white',
                'padding': '30px',
                'boxShadow': '0 0 10px rgba(0,0,0,0.25)',
                'textAlign': 'center',
                'z-index': 9999
            })
        ],
)

    numero = dados ['viatura']
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
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),

        dcc.Store(id='oc-store', data=id),

        html.Div([
            html.H3(f"{dados['nomenclatura']}", className='tittle'),

            html.Div([
                html.Div([
                    html.P(
                        f"Descrição: {dados.get('descricao', 'Não informada.') or 'Não informada.'}",
                        className='det desc'
                    ),
                    html.P(
                        f"Endereço: {dados.get('endereco', 'Não informado.') or 'Não informado.'}",
                        className='det ende'
                    ),
                    html.P(
                        f"Cidadão atendido: {dados.get('n_cidadao', 'Não informado.') or 'Não informado.'}",
                        className='det cid'
                    ),
                    html.P(
                        f"contato do cidadão: {dados.get('contato', 'Não informado.') or 'Não informado.'}",
                        className='det tel'
                    ),
                    dcc.Link(
                        html.P(f"Veículo: {dados['viatura']}", className='det viat'),
                        href=f"/dashboard/veiculo/{dates['numero']}" if dates else '#',
                        className='link-ag-vt'
                    )
                ], className='texts-det'),
            ], className='details-items'),

            html.Div([
                html.Div([
                    html.A(id='rem_agent', children='Remover Ocorrência', className='btn rem_vehicle')
                ], className='btn_rem'),

                html.Div([
                    html.A(id='pdf_oco_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf'),
            ], className='btn_rem_pdf'),

        ], className='details-container'),

        html.Div([
            html.H4(f"Ocorrências do veículo {dados['viatura']}"),
            dcc.Dropdown(
                id='filter-month',
                options=dropdown_options,
                value='todos',
                placeholder="Filtrar por mês...",
                className='filter-month'
            ),
            html.Div(id='table-oco-viat'),
            html.Div([
                html.A(id='detalhes-oco-serv-pdf', children='Gerar PDF', target="_blank", className='btn-pdf')
            ], style={'margin-bottom': '2rem'}),
        ], className='ocurrences'),

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


        ], className='agents-container'),

    ], className='page-content')

@callback(
    Output('n_oco_popup', 'pathname'),
    Input('botao-voltar', 'n_clicks'),
    prevent_initial_call=True
)
def voltar(n_clicks):
    return '/dashboard/ocurrences'

@callback(
    Output('table-oco-viat', 'children'),
    Input('filter-month', 'value'),
    Input('oc-store', 'data')
)
def att_tabela_oco(mes, ocorrencia_id):

    ocorrencia = next((v for v in Ocur_Vehicles if v['id'] == ocorrencia_id), None)
    if not ocorrencia:
        return html.P("Sem ocorrências anteriores.")

    numero_viatura = ocorrencia.get('viatura')
    ocorrencias_viatura = [o for o in Ocur_Vehicles if o.get('viatura') == numero_viatura]


    if mes != 'todos':
        ocorrencias_viatura = [
            o for o in ocorrencias_viatura
            if datetime.strptime(o['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]

    if not ocorrencias_viatura:
        return html.P("Nenhuma ocorrência registrada para este período.")

    return html.Table([
        html.Thead(
            html.Tr([
                html.Th("Data"),
                html.Th("Tipo")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(o.get('data', 'Não informada')),
                html.Td(o.get('nomenclatura', 'Não informada')),
                dcc.Link(
                    html.Td('Ver Mais', className='bt'),
                    href=f"/dashboard/ocurrences/{o['id']}",
                    className="btn_view"
                )
            ]) for o in ocorrencias_viatura
        ])
    ], className='table-ocurrences-serv')

@callback(
    Output('detalhes-oco-serv-pdf', 'href'),
    Input('filter-month', 'value'),
    Input('oc-store', 'data')
)
def oco_detalhes_pdf(filtro_status, ocorrencia_id):
    ocorrencia = next((o for o in Ocur_Vehicles if o['id'] == ocorrencia_id), None)
    if not ocorrencia:
        return "#"

    numero_viatura = ocorrencia.get('viatura')
    return f"/pdf_detalhes_viatura_{numero_viatura}?status={filtro_status}"

@callback(
    Output('pdf_oco_serv_det_gerar', 'href'),
    Input('oc-store', 'data')
)
def oco_det_pdf(ocorrencia_id):
    ocorrencia = next((o for o in Ocur_Vehicles if o['id'] == ocorrencia_id), None)
    if not ocorrencia:
        return "#"
    return f"/pdf_detalhes_ocorrencia_{ocorrencia_id}"