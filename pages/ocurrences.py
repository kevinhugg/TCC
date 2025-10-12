import dash
from dash import html, dcc, Input, Output, callback, State, no_update, ctx
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd
import sys
import os
import urllib.parse

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from firebase_functions import get_all_occurrences, add_occurrence, get_all_occurrence_types, add_occurrence_type, get_all_agents, get_all_vehicles, delete_occurrence
    FIREBASE_AVAILABLE = True
except ImportError as e:
    FIREBASE_AVAILABLE = False
    
    def get_all_occurrences():
        return []
    
    def add_occurrence(data):
        return False, "Firebase não disponível"
    
    def get_all_occurrence_types():
        return [{'id': '1', 'tipo': 'Manutenção'}, {'id': '2', 'tipo': 'Acidente'}]
    
    def add_occurrence_type(data):
        return False, "Firebase não disponível"
    
    def get_all_agents():
        return []
    
    def get_all_vehicles():
        return []
    
    def delete_occurrence(agent_id, date, occurrence_id):
        return False

dash.register_page(__name__, path='/ocurrences', name='Ocorrências')

def get_page_data():
    try:
        ocorrencias = get_all_occurrences()
        return ocorrencias
    except Exception as e:
        return []

def layout():
    ocorrencias = get_page_data()
    
    try:
        occurrence_types_fb = get_all_occurrence_types()
    except Exception as e:
        occurrence_types_fb = []

    occurrence_types_table = html.Table([
        html.Thead(html.Tr([html.Th("Tipos de Ocorrência")])),
        html.Tbody([
            html.Tr([html.Td(ot['tipo'])]) for ot in occurrence_types_fb
        ])
    ], className='serv-table')

    occurrence_types_container = html.Div([
        html.H4("Tipos de Ocorrência"),
        html.Div(occurrence_types_table, className='service-types-list'),
        html.A('Adicionar Tipo', id='add-occurrence-type-btn', className='btn_add')
    ], className='graph_tipes card')

    if ocorrencias:
        meses_unicos = sorted(list(set(
            datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
            for o in ocorrencias if o.get('data')
        )))
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
            {'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(), 'value': m}
            for m in meses_unicos
        ]
    else:
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}]

    confirm_remove_occurrences = dcc.ConfirmDialog(
        id='confirm-remove-occurrences',
        message='Deseja realmente apagar as ocorrências selecionadas?',
    )

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/styleOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='filtro-search-oco'),
        dcc.Location(id='url-occurrences', refresh=True),
        dcc.Store(id='selected-occurrences', data=[]),
        dcc.Store(id='edit-mode-occurrences', data=False),
        dcc.Interval(
            id='interval-occurrences',
            interval=10*1000,
            n_intervals=0
        ),

        confirm_remove_occurrences,

        html.Div([
            html.Div([
                html.Div([
                    html.H3('Ocorrências Gerais', className='title'),
                    html.Div([
                        dcc.Input(id='input-search-oco', type='text', placeholder='Buscar por tipo ou viatura...',
                                  className='input-search'),
                        dcc.Dropdown(
                            id='filter-month-oco',
                            options=dropdown_options,
                            value='todos',
                            placeholder="Filtrar por mês...",
                            className='filter-month'
                        ),
                    ], className='search-controls'),
                ], className='searchbar'),

                html.Table([
                    html.Thead(html.Tr([
                        html.Th('Selecionar', id='select-header-occurrences', style={'display': 'none'}),
                        html.Th('Data'), 
                        html.Th('Responsável'), 
                        html.Th('Tipo'),
                        html.Th('Veículo'), 
                        html.Th('Ações')
                    ])),
                    html.Tbody(id='oco-table')
                ], className='oco-table'),

                html.Div([
                    html.Button(id='rem_oco', children='Apagar Ocorrências', className='rem_serv btn-danger'),
                    html.Div(
                        html.A(id='pdf_oco_gerar', children='Gerar PDF', target="_blank", className='btn-pdf'),
                        className='btn-pdf-oco'
                    ),
                ], className='btn_rem_add_pdf'),

            ], className='oco_serv_container card'),
            html.Div([
                occurrence_types_container
            ], className='graph-and-table-container'),
        ]),

        html.Div(id='modal-add-occurrence-type', className='modal', style={'display': 'none'}, children=[
            html.Div(className='modal-content', children=[
                html.Div(className='modal-header', children=[
                    html.H5('Adicionar Novo Tipo de Ocorrência', className='modal-title'),
                    html.Button('×', id='modal-add-occurrence-type-close', n_clicks=0, className='modal-close-button'),
                ]),
                html.Div(className='modal-body', children=[
                    dcc.Input(id='input-new-occurrence-type-name', type='text',
                              placeholder='Nome do tipo de ocorrência',
                              className='modal-input'),
                ]),
                html.Div(className='modal-footer', children=[
                    html.Button('Salvar', id='save-new-occurrence-type-btn', className='modal-button submit'),
                ])
            ])
        ]),
    ], className='page-content')

def remover_acentos(txt):
    if not txt:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()

@callback(
    Output('oco-table', 'children'),
    Output('pdf_oco_gerar', 'href'),
    Output('select-header-occurrences', 'style'),
    Input('input-search-oco', 'value'),
    Input('filter-month-oco', 'value'),
    Input('edit-mode-occurrences', 'data'),
    Input('url-occurrences', 'pathname'),
    Input('interval-occurrences', 'n_intervals'),
    prevent_initial_call=True
)
def update_occurrence_table(search_value, mes, edit_mode, pathname, n_intervals):
    ocorrencias = get_page_data()
    
    if not ocorrencias:
        col_span = 6 if edit_mode else 5
        return html.Tr([
            html.Td("Nenhuma ocorrência encontrada.", colSpan=col_span, className='not-found'),
        ]), "/gerar_pdf_ocorrencias", {'display': 'none'}

    if mes != 'todos':
        filtered = [
            item for item in ocorrencias
            if item.get('data') and datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]
    else:
        filtered = ocorrencias

    if search_value:
        search_term = remover_acentos(search_value)
        filtered_by_search = []
        for item in filtered:
            if (search_term in remover_acentos(item.get('viatura', '')) or 
                search_term in remover_acentos(item.get('tipo_ocorrencia', '')) or 
                search_term in remover_acentos(item.get('responsavel', ''))):
                filtered_by_search.append(item)
        filtered = filtered_by_search

    if not filtered:
        col_span = 6 if edit_mode else 5
        return html.Tr([
            html.Td("Ocorrência não encontrada!", colSpan=col_span, className='not-found'),
        ]), f"/gerar_pdf_ocorrencias?filtro={search_value or ''}&mes={mes or ''}", {'display': 'none'}

    rows = []
    for item in filtered:
        agent_id = item.get('responsavel_id', '')
        agent_name = item.get('responsavel', 'N/A')
        viatura = item.get('viatura', 'N/A')
        occurrence_id = item.get('id', '')

        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'occurrence-select', 'index': occurrence_id},
                options=[{'label': '', 'value': occurrence_id}],
                value=[],
                className='occurrence-checkbox'
            ),
            style={'display': 'table-cell' if edit_mode else 'none'}
        )

        try:
            data_formatada = datetime.strptime(item['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            data_formatada = item['data']

        encoded_id = urllib.parse.quote(occurrence_id, safe='')

        cells = [
            checkbox_cell,
            html.Td(data_formatada),
            html.Td(
                dcc.Link(agent_name, href=f"/dashboard/agent/{agent_id}") if agent_id else agent_name,
                className='btn_ag'
            ),
            html.Td(item.get('tipo_ocorrencia', 'N/A')),
            html.Td(
                dcc.Link(viatura, href=f"/dashboard/veiculo/{viatura}"),
                className='btn_veh'
            ),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/ocurrences/{encoded_id}", className='btn_view')
            ),
        ]

        row = html.Tr(cells)
        rows.append(row)

    pdf_link = f"/gerar_pdf_ocorrencias?filtro={search_value or ''}&mes={mes or ''}"
    header_style = {'display': 'table-cell' if edit_mode else 'none'}
    
    return rows, pdf_link, header_style

@callback(
    Output('selected-occurrences', 'data', allow_duplicate=True),
    Input({'type': 'occurrence-select', 'index': dash.ALL}, 'value'),
    prevent_initial_call=True
)
def update_selected_occurrences(selected_values):
    selected = [item for sublist in selected_values for item in sublist if sublist]
    return selected

@callback(
    Output('edit-mode-occurrences', 'data'),
    Output('rem_oco', 'children'),
    Input('rem_oco', 'n_clicks'),
    State('edit-mode-occurrences', 'data'),
    prevent_initial_call=True
)
def toggle_edit_mode(n_clicks, current_mode):
    if n_clicks:
        new_mode = not current_mode
        button_text = "Confirmar Remoção" if new_mode else "Apagar Ocorrências"
        return new_mode, button_text
    return current_mode, "Apagar Ocorrências"

@callback(
    Output('confirm-remove-occurrences', 'displayed'),
    Input('rem_oco', 'n_clicks'),
    State('selected-occurrences', 'data'),
    State('edit-mode-occurrences', 'data'),
    prevent_initial_call=True
)
def confirm_removal(n_clicks, selected_occurrences, edit_mode):
    if n_clicks and edit_mode and selected_occurrences:
        return True
    return False

@callback(
    Output('url-occurrences', 'pathname', allow_duplicate=True),
    Output('selected-occurrences', 'data', allow_duplicate=True),
    Output('edit-mode-occurrences', 'data', allow_duplicate=True),
    Input('confirm-remove-occurrences', 'submit_n_clicks'),
    State('selected-occurrences', 'data'),
    prevent_initial_call=True
)
def remove_selected_occurrences(submit_clicks, selected_occurrences):
    if submit_clicks and selected_occurrences:
        success_count = 0
        error_count = 0
        
        for occurrence_id in selected_occurrences:
            if FIREBASE_AVAILABLE:
                ocorrencias = get_all_occurrences()
                ocorrencia = next((occ for occ in ocorrencias if occ.get('id') == occurrence_id), None)
                
                if ocorrencia:
                    agent_id = ocorrencia.get('responsavel_id')
                    date = ocorrencia.get('data')
                    
                    if agent_id and date:
                        success = delete_occurrence(agent_id, date, occurrence_id)
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1
        
        return '/dashboard/ocurrences', [], False
    
    return no_update, no_update, no_update

@callback(
    Output('modal-add-occurrence-type', 'style'),
    [Input('add-occurrence-type-btn', 'n_clicks'),
     Input('modal-add-occurrence-type-close', 'n_clicks'),
     Input('save-new-occurrence-type-btn', 'n_clicks')],
    State('modal-add-occurrence-type', 'style'),
    prevent_initial_call=True,
)
def toggle_modal(n1, n2, n3, style_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        return style_type

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-occurrence-type-btn':
        return {'display': 'block'}

    if button_id in ['modal-add-occurrence-type-close', 'save-new-occurrence-type-btn']:
        return {'display': 'none'}

    return style_type

@callback(
    [Output('url-occurrences', 'pathname', allow_duplicate=True),
     Output('input-new-occurrence-type-name', 'value')],
    Input('save-new-occurrence-type-btn', 'n_clicks'),
    State('input-new-occurrence-type-name', 'value'),
    prevent_initial_call=True
)
def save_new_occurrence_type(n_clicks, name):
    if n_clicks and name:
        try:
            occurrence_data = {
                'tipo': name.strip()  
            }
            
            success, message = add_occurrence_type(occurrence_data)
            
            if success:
                return '/dashboard/ocurrences', ''
                
        except Exception as e:
            pass
    
    return dash.no_update, dash.no_update

@callback(
    Output('filtro-search-oco', 'data'),
    Input('interval-occurrences', 'n_intervals')
)
def debug_data_loading(n_intervals):
    ocorrencias = get_page_data()
    return {'count': len(ocorrencias)}

@callback(
    Output('url-occurrences', 'pathname', allow_duplicate=True),
    Input('oco-table', 'children'),
    State('url-occurrences', 'pathname'),
    prevent_initial_call=True
)
def debug_navigation(table_children, current_path):
    return dash.no_update