import dash
from dash import html, dcc, Input, Output, callback, State
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd

from data.dados import agents, Ocur_Vehicles, occurrence_types

dash.register_page(__name__, path='/ocurrences', name='Ocorrências', className='pg-at')

item = next((v for v in Ocur_Vehicles))
responsavel = next((a['nome'] for a in agents if a['viatura_mes'] == item['viatura']), 'Desconhecido')
respon_id = next((a['id'] for a in agents if a['viatura_mes'] == item['viatura']), 'Desconhecido')
viat_func = next((a['viatura_mes'] for a in agents))
meses_unicos = sorted(set(
    datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
    for o in Ocur_Vehicles if o['viatura'] == viat_func
))

ocorrencias = [o for o in Ocur_Vehicles if o.get('class') == 'ocorrencia']

dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
    {
        'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(),
        'value': m
    } for m in meses_unicos
]

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleOcurrencesServices.css'),
    html.Link(rel='stylesheet', href='/static/css/modal.css'),
    dcc.Location(id='url-occurrences', refresh=True),
    dcc.Store(id='filtro-search'),

    html.Div([

        html.Div([

            html.Div([
                html.H3('Ocorrências Gerais', className='title'),
                dcc.Dropdown(
                    id='filter-month',
                    options=dropdown_options,
                    value='todos',
                    placeholder="Filtrar por mês...",
                    className='filter-month'
                ),
                dcc.Input(id='input-search', type='text', placeholder='Buscar por responsável ou viatura...',
                          className='input-search'),
            ], className='searchbar'),

            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Data'),
                        html.Th('Responsável'),
                        html.Th('Tipo'),
                        html.Th('Veículo'),
                    ])
                ]),
                html.Tbody(id='oco-table', children=[
                    html.Tr([
                        html.Td(item['data']),
                        html.Td(
                            dcc.Link(responsavel, href=f"/dashboard/agent/{respon_id}"), className='btn_ag'
                        ),
                        html.Td(item['nomenclatura']),
                        html.Td(
                            dcc.Link(item['viatura'], href=f"/dashboard/veiculo/{item['viatura']}"), className='btn_veh'
                        ),
                        html.Td(
                            dcc.Link('Ver Mais', href=f"/dashboard/ocurrences/{item['id']}"), className='btn_view'
                        ),
                    ])
                    for item in Ocur_Vehicles
                ])
            ], className='oco-table'),

            html.Div([
                html.Div([
                    html.A(id='rem_oco', children='Apagar Ocorrências', className='rem_serv btn-danger')
                ], className='btn'),

                html.Div([
                    html.A(id='pdf_oco_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf-oco'),
            ], className='btn_rem_add_pdf'),

        ], className='oco_serv_container'),
    ]),

    html.Div([
        html.H4("Tipos de Ocorrência"),
        html.Table([
            html.Thead(html.Tr([html.Th("Tipos de Ocorrência")])),
            html.Tbody([
                html.Tr([html.Td(ot['nome'])]) for ot in occurrence_types
            ])
        ], className='serv-table'),
        html.A('Adicionar Tipo', id='add-occurrence-type-btn', className='btn_add')
    ], className='graph_tipes card'),

    html.Div(id='modal-add-occurrence-type', className='modal', style={'display': 'none'}, children=[
        html.Div(className='modal-content', children=[
            html.Div(className='modal-header', children=[
                html.H5('Adicionar Novo Tipo de Ocorrência', className='modal-title'),
                html.Button('×', id='modal-add-occurrence-type-close', n_clicks=0, className='modal-close-button'),
            ]),
            html.Div(className='modal-body', children=[
                dcc.Input(id='input-new-occurrence-type-name', type='text', placeholder='Nome do tipo de ocorrência',
                          className='modal-input'),
            ]),
            html.Div(className='modal-footer', children=[
                html.Button('Salvar', id='save-new-occurrence-type-btn', className='modal-button submit'),
            ])
        ])
    ]),
], className='page-content')


@callback(
    Output('modal-add-occurrence-type', 'style'),
    [Input('add-occurrence-type-btn', 'n_clicks'),
     Input('modal-add-occurrence-type-close', 'n_clicks'),
     Input('save-new-occurrence-type-btn', 'n_clicks')],
    [State('modal-add-occurrence-type', 'style')],
    prevent_initial_call=True,
)
def toggle_modal(n1, n2, n3, style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return style

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-occurrence-type-btn':
        return {'display': 'block'}

    if button_id in ['modal-add-occurrence-type-close', 'save-new-occurrence-type-btn']:
        return {'display': 'none'}

    return style


@callback(
    Output('url-occurrences', 'pathname'),
    Input('save-new-occurrence-type-btn', 'n_clicks'),
    State('input-new-occurrence-type-name', 'value'),
    prevent_initial_call=True
)
def save_new_occurrence_type(n_clicks, name):
    if n_clicks and name:
        new_id = max(ot['id'] for ot in occurrence_types) + 1 if occurrence_types else 1
        occurrence_types.append({'id': new_id, 'nome': name})

        with open('data/dados.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_index = -1
        for i, line in enumerate(lines):
            if 'occurrence_types = [' in line:
                start_index = i
                break

        if start_index != -1:
            end_index = start_index
            bracket_count = 0
            for i, line in enumerate(lines[start_index:]):
                bracket_count += line.count('[')
                bracket_count -= line.count(']')
                if bracket_count == 0:
                    end_index = start_index + i
                    break

            new_list_str = "occurrence_types = [\n"
            for ot in occurrence_types:
                new_list_str += f"    {{'id': {ot['id']}, 'nome': '{ot['nome']}'}},\n"
            new_list_str += "]\n"

            lines = lines[:start_index] + [new_list_str] + lines[end_index + 1:]

            with open('data/dados.py', 'w', encoding='utf-8') as f:
                f.writelines(lines)

        return '/dashboard/ocurrences'
    return dash.no_update


def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()


@callback(
    Output('oco-table', 'children'),
    Output('pdf_oco_gerar', 'href'),
    Input('input-search', 'value'),
    Input('filter-month', 'value'),
)
def update_list(search_value, mes):
    if not search_value:
        filtered = ocorrencias
    else:
        search_value = remover_acentos(search_value.lower())
        filtered = [
            item for item in ocorrencias
            if search_value in remover_acentos(item['viatura'].lower()) or
               any(search_value in remover_acentos(a['nome'].lower()) for a in agents if
                   a['viatura_mes'] == item['viatura'])
        ]

    if mes != 'todos':
        filtered = [
            item for item in filtered
            if datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]

    if not filtered:
        return html.Tr([
            html.Td("Ocorrência não encontrada!", colSpan=5, className='not-found'),
        ]), f"/gerar_pdf_ocorrencias?filtro={search_value}&mes={mes}"

    rows = []
    for item in filtered:
        responsavel = next((a['nome'] for a in agents if a['viatura_mes'] == item['viatura']), 'Desconhecido')
        respon_id = next((a['id'] for a in agents if a['viatura_mes'] == item['viatura']), 'Desconhecido')
        row = html.Tr([
            html.Td(item['data']),
            html.Td(
                dcc.Link(responsavel, href=f"/dashboard/agent/{respon_id}"), className='btn_ag'
            ),
            html.Td(item['nomenclatura']),
            html.Td(
                dcc.Link(item['viatura'], href=f"/dashboard/veiculo/{item['viatura']}"), className='btn_veh'
            ),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/ocurrences/{item['id']}"), className='btn_view'
            ),
        ])
        rows.append(row)

    pdf_link = f"/gerar_pdf_ocorrencias?filtro={search_value}&mes={mes}"

    return rows, pdf_link