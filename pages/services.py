import dash
from dash import html, dcc, Input, Output, callback, State, ctx
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd
import dash_bootstrap_components as dbc
import firebase_functions as fb

dash.register_page(__name__, path='/services', name='Serviços', className='pg-at')


def remover_acentos(txt):
    if not txt:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def get_page_data():
    """Fetches and prepares all data needed for the services page."""
    try:
        all_items = fb.get_all_occurrences_and_services()
        all_agents = fb.get_all_agents()

        # Filter for services only
        servicos = [s for s in all_items if s.get('class') == 'serviço']

        # Create a mapping from vehicle number to responsible agent for efficient lookup
        agent_map = {}
        for agent in all_agents:
            vehicle = agent.get('viatura')
            if vehicle and agent.get('funcao') in ['Encarregado', 'Motorista']:
                if vehicle not in agent_map:
                    agent_map[vehicle] = {'nome': agent.get('nome'), 'id': agent.get('id')}

        return servicos, agent_map
    except Exception as e:
        print(f"Error fetching data for services page: {e}")
        return [], {}


def layout():
    servicos, _ = get_page_data()

    if servicos:
        meses_unicos = sorted(list(set(
            datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
            for o in servicos
        )))
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
            {
                'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(),
                'value': m
            } for m in meses_unicos
        ]
    else:
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/styleOcurrencesServices.css'),
        dcc.Store(id='filtro-search-serv'),

        html.Div([
            html.Div([
                html.Div([
                    html.H3('Serviços Gerais', className='title'),
                    dcc.Dropdown(
                        id='filter-month-serv',
                        options=dropdown_options,
                        value='todos',
                        placeholder="Filtrar por mês...",
                        className='filter-month'
                    ),
                    dcc.Input(id='input-search-serv', type='text', placeholder='Buscar por tipo ou viatura...',
                              className='input-search'),
                ], className='searchbar'),

                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th('Data'),
                            html.Th('Responsável'),
                            html.Th('Tipo'),
                            html.Th('Veículo'),
                            html.Th('Ações'),
                        ])
                    ]),
                    html.Tbody(id='serv-table')
                ], className='serv-table'),

                html.Div([
                    html.Div([
                        html.A(id='rem_serv', children='Apagar Serviços', className='rem_serv btn-danger')
                    ], className='btn'),
                    html.Div([
                        html.A(id='pdf_serv_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                    ], className='btn-pdf-serv'),
                ], className='btn_rem_add_pdf'),

            ], className='oco_serv_container card'),
        ]),

        html.Div([
            dcc.Graph(id='fig_serv_tipos', className='fig_serv'),
            html.Div([
                html.Div([
                    html.A(id='add_serv', children='Adicionar Serviço', className='btn_add')
                ], className='btn'),
            ], className='btn_rem_add_pdf'),
        ], className='graph_tipes card'),
    ], className='page-content')


@callback(
    Output('serv-table', 'children'),
    Output('pdf_serv_gerar', 'href'),
    Input('input-search-serv', 'value'),
    Input('filter-month-serv', 'value'),
)
def update_list(search_value, mes):
    servicos, agent_map = get_page_data()

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
            responsavel = agent_map.get(item.get('viatura'), {})
            responsavel_nome = remover_acentos(responsavel.get('nome', ''))

            if search_term in remover_acentos(item.get('viatura', '')) or \
                    search_term in remover_acentos(item.get('nomenclatura', '')) or \
                    search_term in responsavel_nome:
                filtered_by_search.append(item)
        filtered = filtered_by_search

    if not filtered:
        return html.Tr([
            html.Td("Serviço não encontrado!", colSpan=5, className='not-found'),
        ]), f"/gerar_pdf_servicos_gerais?filtro={search_value}&mes={mes}"

    rows = []
    for item in filtered:
        responsavel = agent_map.get(item.get('viatura'), {'nome': 'N/A', 'id': ''})
        row = html.Tr([
            html.Td(item.get('data', 'N/A')),
            html.Td(
                dcc.Link(responsavel['nome'], href=f"/dashboard/agent/{responsavel['id']}") if responsavel['id'] else
                responsavel['nome'],
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
    Input('theme-mode', 'data')
)
def update_graph(mes, theme):
    servicos, _ = get_page_data()

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

    is_dark = theme == 'dark'
    bar_color = '#60a5fa' if is_dark else '#4682B4'
    title_color = '#f9fafb' if is_dark else '#295678'
    bg_color = 'rgba(0,0,0,0)'

    fig_tipos = px.bar(
        df_servicos,
        x='Tipo',
        y='Quantidade',
        text='Quantidade',
        labels={'Tipo': '', 'Quantidade': ''},
        title='Serviços Cadastrados'
    )

    fig_tipos.update_traces(marker_color=bar_color, textposition='outside')
    fig_tipos.update_layout(
        title={'text': 'Serviços Cadastrados'},
        title_font_size=26,
        title_font_color=title_color,
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font_color=title_color
    )
    return fig_tipos