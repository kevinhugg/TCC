import dash
from dash import html, dcc, Input, Output, callback

from data.dados import agents, viaturas

dash.register_page(__name__, path='/pageAgents', name='Agentes')

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleAgents.css'),

    dcc.Store(id='filtro-search'),

    html.Div([

        html.Div([

            html.Div([
                dcc.Input(id='input-search', type='text', placeholder='Buscar por nome ou função...', className='input-search'),
            ], className='searchbar'),

            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Nome'),
                        html.Th('Cargo'),
                        html.Th('Função'),
                        html.Th('Veículo'),
                    ])
                ]),
                html.Tbody(id='agents-table', children=[
                    html.Tr([
                        html.Td(item['nome']),
                        html.Td(item['cargo_at']),
                        html.Td(item['func_mes']),
                        html.Td(
                            dcc.Link(item['viatura_mes'], href=f"/dashboard/veiculo/{item['viatura_mes']}"), className='btn_veh'
                        ),
                        html.Td(
                            dcc.Link('Ver Mais', href=f"/dashboard/agent/{item['nome']}"), className='btn_view'
                        ),
                    ])
                    for item in agents
                ])
            ], className='agents-table'),



            html.Div([
                html.Div([
                    html.A(id='rem_agents', children='Remover Agentes', className='rem_agents')
                ], className='btn'),

                html.Div([
                   html.A(id='pdf_agentes_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf-agent'),

                html.Div([
                    html.A(id='add_agents', children='Adicionar Agente', className='add_agents')
                ], className='btn'),
            ], className='btn_rem_add_pdf'),

        ], className='agents_container card'),
    ])

], className='page-content')

@callback(
    Output('agents-table', 'children'),
    Output('pdf_agentes_gerar', 'href'),
    Input('input-search', 'value')
)
def update_list(search_value):
    if not search_value:
        filtered = agents
    else:
        search_value = search_value.lower()
        filtered = [
            a for a in agents
            if search_value in a['nome'].lower() or search_value in a['func_mes'].lower() or search_value in a['cargo_at'].lower()
        ]

    if not filtered:
        return html.Tr([
            html.Td("Agente não encontrado!", colSpan=5, className='not-found'),
        ]), f"/gerar_pdf_agentes?filtro={search_value}"

    rows = [
        html.Tr([
            html.Td(item['nome']),
            html.Td(item['cargo_at']),
            html.Td(item['func_mes']),
            html.Td([
                dcc.Link(item['viatura_mes'], href=f"/dashboard/veiculo/{item['viatura_mes']}")
            ], className='btn_veh'),
            html.Td([
                dcc.Link('Ver Mais', href=f"/dashboard/agent/{item['id']}")
            ], className='btn_view'),
        ])
        for item in filtered
    ]

    pdf_link = f"/gerar_pdf_agentes?filtro={search_value}" if search_value else "/gerar_pdf_agentes"

    return rows, pdf_link