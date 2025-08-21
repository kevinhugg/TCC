import dash
from dash import html, dcc, Input, Output, callback, State
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd

from data.dados import Ocur_Vehicles, agents, service_types

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

    service_types_table = html.Table([
        html.Thead(html.Tr([html.Th("Tipos de Serviço")])),
        html.Tbody([
            html.Tr([html.Td(st['nome'])]) for st in service_types
        ])
    ], className='serv-table')

    service_types_container = html.Div([
        html.H4("Tipos de Serviço"),
        html.Div(service_types_table, className='service-types-list'),
        html.A('Adicionar Tipo', id='add-service-type-btn', className='btn_add')
    ], className='graph_tipes card')

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
            html.Div([
                service_types_container
            ], className='graph-and-table-container'),
        ]),

        html.Div(id='modal-add-service-type', className='modal', style={'display': 'none'}, children=[
            html.Div(className='modal-content', children=[
                html.Div(className='modal-header', children=[
                    html.H5('Adicionar Novo Tipo de Serviço', className='modal-title'),
                    html.Button('×', id='modal-add-service-type-close', n_clicks=0, className='modal-close-button'),
                ]),
                html.Div(className='modal-body', children=[
                    dcc.Input(id='input-new-service-type-name', type='text', placeholder='Nome do tipo de serviço',
                              className='modal-input'),
                ]),
                html.Div(className='modal-footer', children=[
                    html.Button('Salvar', id='save-new-service-type-btn', className='modal-button submit'),
                ])
            ])
        ]),
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
            responsavel_info = next((agent for agent in agents if agent.get('viatura_mes') == item.get('viatura')),
                                    None)
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
    Output('modal-add-service-type', 'style'),
    [Input('add-service-type-btn', 'n_clicks'),
     Input('modal-add-service-type-close', 'n_clicks'),
     Input('save-new-service-type-btn', 'n_clicks')],
    [State('modal-add-service-type', 'style')],
    prevent_initial_call=True,
)
def toggle_modal(n1, n2, n3, style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return style

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-service-type-btn':
        return {'display': 'block'}

    if button_id in ['modal-add-service-type-close', 'save-new-service-type-btn']:
        return {'display': 'none'}

    return style


@callback(
    Output('url-services', 'pathname'),
    Input('save-new-service-type-btn', 'n_clicks'),
    State('input-new-service-type-name', 'value'),
    prevent_initial_call=True
)
def save_new_service_type(n_clicks, name):
    if n_clicks and name:
        # Atualiza a lista em memória
        new_id = max(st['id'] for st in service_types) + 1 if service_types else 1
        service_types.append({'id': new_id, 'nome': name})

        # Lê o conteúdo do arquivo
        with open('data/dados.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Encontra a linha onde a lista service_types é definida
        start_index = -1
        for i, line in enumerate(lines):
            if 'service_types = [' in line:
                start_index = i
                break

        if start_index != -1:
            # Encontra o final da lista
            end_index = start_index
            bracket_count = 0
            for i, line in enumerate(lines[start_index:]):
                bracket_count += line.count('[')
                bracket_count -= line.count(']')
                if bracket_count == 0:
                    end_index = start_index + i
                    break

            # Recria a string da lista
            new_list_str = "service_types = [\n"
            for st in service_types:
                new_list_str += f"    {{'id': {st['id']}, 'nome': '{st['nome']}'}},\n"
            new_list_str += "]\n"

            # Substitui a lista antiga pela nova
            lines = lines[:start_index] + [new_list_str] + lines[end_index + 1:]

            # Escreve o conteúdo de volta no arquivo
            with open('data/dados.py', 'w', encoding='utf-8') as f:
                f.writelines(lines)

        return '/dashboard/services'
    return dash.no_update