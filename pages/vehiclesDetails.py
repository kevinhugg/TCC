import dash
from dash import html, dcc, Input, Output, callback
from datetime import datetime

from data.dados import viaturas, Ocur_Vehicles, agents

dash.register_page(__name__, path_template='/veiculo/<numero>', name=None)

def layout(numero=None):
    dados = next((v for v in viaturas if v['numero'] == numero), None)

    resp_veh = [a for a in agents if a['viatura_mes'] == numero]
    motorista = next((a for a in resp_veh if a['func_mes'].lower() == 'motorista'), None)
    another_agents = [a for a in resp_veh if a !=motorista]

    if not(dados):
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

        dcc.Store(id='vehicle-store', data=numero),

        html.Div([
            html.H3(f"Viatura - {dados['numero']}", className='tittle'),

            html.Div([
                html.Img(src=dados['imagem'], className='img'),
                html.Div([
                    html.P(f"Placa: {dados['placa']}", className='det placa'),
                    html.P(f"Tipo: {dados['veiculo']}", className='det tipo'),
                    html.P(f"Situação: {'Avariada' if dados['avariada'] else 'Operante'}", className='det avariada' if dados['avariada'] else 'det operante'),
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
            #colocar um icone para filtrar aqui por local da avaria, ocorrencia ou serviço
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
            html.H3(f"Responsáveis do Mês", className='tittle'),

            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=motorista['foto_agnt'] if motorista else '/static/img/default-user.png', className='img'),
                        html.P(f"{motorista['nome']}" if motorista else "Motorista não encontrado", className='agent-name'),
                        html.P(f"Função: {motorista['func_mes'].capitalize()}" if motorista else "", className='agent-role'),
                        html.P(f"{motorista['cargo_at']}" if motorista else "", className='agent-cargo'),
                    ], className='agent-box motorista'),
                href=f"/dashboard/agent/{motorista['id']}", className='link-ag-vt'
                ) if motorista else [],

                *[
                    dcc.Link(
                        html.Div([
                            html.Img(src=agente['foto_agnt'], className='img'),
                            html.P(f"{agente['nome']}", className='agent-name'),
                            html.P(f"Função: {agente['func_mes'].capitalize()}", className='agent-role'),
                            html.P(f"{agente['cargo_at']}", className='agent-cargo'),
                        ], className='agent-box'),
                        href=f"/dashboard/agent/{agente['id']}", className = 'link-ag-vt'
                    ) for agente in another_agents
                ]
            ], className='agents-grid'),

        ], className='agents-container card'),

    ], className='page-content')


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