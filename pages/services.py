import dash
from dash import html, dcc, Input, Output, callback
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd

from data.dados import Ocur_Vehicles, agents

dash.register_page(__name__, path='/services', name='Serviços', className='pg-at')


def remover_acentos(txt):
    if not txt:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def get_page_data():
    """Fetches and prepares all data needed for the services page from data/dados.py."""
    try:
        servicos = [o for o in Ocur_Vehicles if o.get('class') == 'serviço']
        return servicos
    except Exception as e:
        print(f"Error fetching data for services page from dados.py: {e}")
        return []


def layout():
    servicos = get_page_data()

    if servicos:
        meses_unicos = sorted(list(set(
            datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
            for o in servicos
        )))
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
            {'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(), 'value': m}
            for m in meses_unicos
        ]
    else:
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/styleOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='filtro-search-serv'),
        dcc.Location(id='url-services', refresh=True),

        html.Div([
            html.Div([
                html.Div([
                    html.H3('Serviços Gerais', className='title'),
                    html.Div([
                        dcc.Input(id='input-search-serv', type='text', placeholder='Buscar por tipo ou viatura...',
                                  className='input-search'),
                        dcc.Dropdown(
                            id='filter-month-serv',
                            options=dropdown_options,
                            value='todos',
                            placeholder="Filtrar por mês...",
                            className='filter-month'
                        ),
                    ], className='search-controls'),
                ], className='searchbar'),

                html.Table([
                    html.Thead(html.Tr([
                        html.Th('Data'), html.Th('Responsável'), html.Th('Tipo'),
                        html.Th('Veículo'), html.Th('Ações')
                    ])),
                    html.Tbody(id='serv-table')
                ], className='serv-table'),

                html.Div([
                    html.Div(
                        html.A(id='rem_serv', children='Apagar Serviços', className='rem_serv btn-danger'),
                        className='btn'
                    ),
                    html.Div(
                        html.A(id='pdf_serv_gerar', children='Gerar PDF', target="_blank", className='btn-pdf'),
                        className='btn-pdf-serv'
                    ),
                ], className='btn_rem_add_pdf'),

            ], className='oco_serv_container card'),
        ]),

        html.Div([
            dcc.Graph(id='fig_serv_tipos', className='fig_serv'),
        ], className='graph_tipes card'),
    ], className='page-content')


@callback(
    Output('serv-table', 'children'),
    Output('pdf_serv_gerar', 'href'),
    Input('input-search-serv', 'value'),
    Input('filter-month-serv', 'value'),
)
def update_list(search_value, mes):
    servicos = get_page_data()

    if not servicos:
        return html.Tr([
            html.Td("Nenhum serviço encontrado.", colSpan=5, className='not-found'),
        ]), "/gerar_pdf_servicos_gerais"

    if mes != 'todos':
        filtered = [
            item for item in servicos
            if datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]
    else:
        filtered = servicos

    if search_value:
        search_term = remover_acentos(search_value)
        filtered_by_search = []
        for item in filtered:
            responsavel_info = next((agent for agent in agents if agent.get('viatura_mes') == item.get('viatura')), None)
            responsavel_nome_item = remover_acentos(responsavel_info['nome']) if responsavel_info else ''

            if search_term in remover_acentos(item.get('viatura', '')) or \
               search_term in remover_acentos(item.get('nomenclatura', '')) or \
               search_term in responsavel_nome_item:
                filtered_by_search.append(item)
        filtered = filtered_by_search

    if not filtered:
        return html.Tr([
            html.Td("Serviço não encontrado!", colSpan=5, className='not-found'),
        ]), f"/gerar_pdf_servicos_gerais?filtro={search_value}&mes={mes}"

    rows = []
    for item in filtered:
        agent_info = next((a for a in agents if a.get('viatura_mes') == item.get('viatura')), None)
        agent_name = agent_info['nome'] if agent_info else 'N/A'
        agent_id = agent_info['id'] if agent_info else ''

        row = html.Tr([
            html.Td(item.get('data', 'N/A')),
            html.Td(
                dcc.Link(agent_name, href=f"/dashboard/agent/{agent_id}") if agent_id else agent_name,
                className='btn_ag'
            ),
            html.Td(item.get('nomenclatura', 'N/A')),
            html.Td(
                dcc.Link(item.get('viatura', 'N/A'), href=f"/dashboard/veiculo/{item.get('viatura', '')}"),
                className='btn_veh'
            ),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/services/{item.get('id', '')}"), className='btn_view'
            ),
        ])
        rows.append(row)

    pdf_link = f"/gerar_pdf_servicos_gerais?filtro={search_value or ''}&mes={mes}"
    return rows, pdf_link


@callback(
    Output('fig_serv_tipos', 'figure'),
    Input('filter-month-serv', 'value'),
)
def update_graph(mes):
    servicos = get_page_data()

    if not servicos:
        return px.bar(title='Nenhum Serviço Cadastrado')

    if mes != 'todos':
        filtered = [
            item for item in servicos
            if datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]
    else:
        filtered = servicos

    tipos = [item['nomenclatura'].strip() for item in filtered]
    contagem_tipos = Counter(tipos)

    if not contagem_tipos:
        return px.bar(title=f'Nenhum serviço em {mes}')

    df_servicos = pd.DataFrame({
        'Tipo': list(contagem_tipos.keys()),
        'Quantidade': list(contagem_tipos.values())
    })

    fig_tipos = px.bar(
        df_servicos,
        x='Tipo',
        y='Quantidade',
        text='Quantidade',
        labels={'Tipo': '', 'Quantidade': ''},
        title='Serviços Cadastrados'
    )

    fig_tipos.update_traces(marker_color='#4682B4', textposition='outside')
    fig_tipos.update_layout(
        title={
            'text': 'Serviços Cadastrados',
            'x': 0.5,
            'xanchor': 'center'
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig_tipos