import dash
from dash import html, dcc, Input, Output, callback, State, no_update
from dash.exceptions import PreventUpdate
import sys
import os
from datetime import datetime
import unicodedata

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from firebase_functions import (
        get_all_services_with_agents, 
        get_all_agents, 
        get_all_service_types, 
        add_service_type,
        delete_service
    )
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

dash.register_page(__name__, path='/services', name='Serviços', className='pg-at')

def remover_acentos(txt):
    if not txt:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def get_page_data():
    try:
        servicos = get_all_services_with_agents()
        return servicos
    except Exception:
        return []

def get_service_types_data():
    try:
        service_types = get_all_service_types()
        return service_types
    except Exception:
        return []

def layout():
    servicos = get_page_data()
    service_types = get_service_types_data()

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
            for o in servicos if o.get('data')
        )))
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
            {'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(), 'value': m}
            for m in meses_unicos
        ]
    else:
        dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}]

    confirm_remove_services = dcc.ConfirmDialog(
        id='confirm-remove-services',
        message='Deseja realmente apagar os serviços selecionados?',
    )

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/styleOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='filtro-search-serv'),
        dcc.Location(id='url-services', refresh=True),
        dcc.Store(id='selected-services', data=[]),
        dcc.Store(id='edit-mode-services', data=False),
        dcc.Interval(
            id='interval-services',
            interval=10*1000,
            n_intervals=0
        ),

        confirm_remove_services,

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
                        html.Th('Selecionar', id='select-header-services', style={'display': 'none'}),
                        html.Th('Data'), 
                        html.Th('Responsável'), 
                        html.Th('Tipo'),
                        html.Th('Veículo'), 
                        html.Th('Ações')
                    ])),
                    html.Tbody(id='serv-table')
                ], className='serv-table'),

                html.Div([
                    html.Button(id='rem_serv', children='Apagar Serviços', className='rem_serv btn-danger'),
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
        
        dcc.Store(id='service-types-store', data=service_types),
    ], className='page-content')

@callback(
    Output('serv-table', 'children'),
    Output('pdf_serv_gerar', 'href'),
    Output('select-header-services', 'style'),
    Input('input-search-serv', 'value'),
    Input('filter-month-serv', 'value'),
    Input('edit-mode-services', 'data'),
    Input('url-services', 'pathname'),
    Input('interval-services', 'n_intervals')
)
def update_list(search_value, mes, edit_mode, pathname, n_intervals):
    servicos = get_page_data()
    agents_data = get_all_agents()

    if not servicos:
        col_span = 6 if edit_mode else 5
        return html.Tr([
            html.Td("Nenhum serviço encontrado.", colSpan=col_span, className='not-found'),
        ]), "/gerar_pdf_servicos_gerais", {'display': 'none'}

    if mes != 'todos':
        filtered = [
            item for item in servicos
            if item.get('data') and datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]
    else:
        filtered = servicos

    if search_value:
        search_term = remover_acentos(search_value)
        filtered_by_search = []
        for item in filtered:
            if (search_term in remover_acentos(item.get('viatura', '')) or 
                search_term in remover_acentos(item.get('nomenclatura', '')) or 
                search_term in remover_acentos(item.get('tipo', '')) or
                search_term in remover_acentos(item.get('responsavel', ''))):
                filtered_by_search.append(item)
        filtered = filtered_by_search

    if not filtered:
        col_span = 6 if edit_mode else 5
        return html.Tr([
            html.Td("Serviço não encontrado!", colSpan=col_span, className='not-found'),
        ]), f"/gerar_pdf_servicos_gerais?filtro={search_value or ''}&mes={mes or ''}", {'display': 'none'}

    rows = []
    for item in filtered:
        agent_id = item.get('responsavel_id', '')
        agent_name = item.get('responsavel', 'N/A')
        viatura = item.get('viatura', 'N/A')
        service_id = item.get('id', '')

        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'service-select', 'index': service_id},
                options=[{'label': '', 'value': service_id}],
                value=[],
                className='service-checkbox'
            ),
            style={'display': 'table-cell' if edit_mode else 'none'}
        )

        cells = [
            checkbox_cell,
            html.Td(item.get('data', 'N/A')),
            html.Td(
                dcc.Link(agent_name, href=f"/dashboard/agent/{agent_id}") if agent_id else agent_name,
                className='btn_ag'
            ),
            html.Td(item.get('nomenclatura', 'N/A')),
            html.Td(
                dcc.Link(viatura, href=f"/dashboard/veiculo/{viatura}"),
                className='btn_veh'
            ),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/services/{item.get('id', '')}", className='btn_view')
            ),
        ]

        row = html.Tr(cells)
        rows.append(row)

    pdf_link = f"/gerar_pdf_servicos_gerais?filtro={search_value or ''}&mes={mes or ''}"
    header_style = {'display': 'table-cell' if edit_mode else 'none'}
    
    return rows, pdf_link, header_style

@callback(
    Output('selected-services', 'data', allow_duplicate=True),
    Input({'type': 'service-select', 'index': dash.ALL}, 'value'),
    prevent_initial_call=True
)
def update_selected_services(selected_values):
    selected = [item for sublist in selected_values for item in sublist if sublist]
    return selected

@callback(
    Output('edit-mode-services', 'data'),
    Output('rem_serv', 'children'),
    Input('rem_serv', 'n_clicks'),
    State('edit-mode-services', 'data')
)
def toggle_edit_mode(n_clicks, current_mode):
    if n_clicks:
        new_mode = not current_mode
        button_text = "Confirmar Remoção" if new_mode else "Apagar Serviços"
        return new_mode, button_text
    return current_mode, "Apagar Serviços"

@callback(
    Output('confirm-remove-services', 'displayed'),
    Input('rem_serv', 'n_clicks'),
    State('selected-services', 'data'),
    State('edit-mode-services', 'data')
)
def confirm_removal(n_clicks, selected_services, edit_mode):
    if n_clicks and edit_mode and selected_services:
        return True
    elif n_clicks and edit_mode and not selected_services:
        return False
    return False

@callback(
    Output('url-services', 'pathname', allow_duplicate=True),
    Output('selected-services', 'data', allow_duplicate=True),
    Output('edit-mode-services', 'data', allow_duplicate=True),
    Input('confirm-remove-services', 'submit_n_clicks'),
    State('selected-services', 'data'),
    prevent_initial_call=True
)
def remove_selected_services(submit_clicks, selected_services):
    if submit_clicks and selected_services:
        success_count = 0
        error_count = 0
        
        for service_id in selected_services:
            if FIREBASE_AVAILABLE:
                success, message = delete_service(service_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
        
        return '/dashboard/services', [], False
    
    return no_update, no_update, no_update

@callback(
    Output('modal-add-service-type', 'style'),
    [Input('add-service-type-btn', 'n_clicks'),
     Input('modal-add-service-type-close', 'n_clicks'),
     Input('save-new-service-type-btn', 'n_clicks')],
    [State('modal-add-service-type', 'style')]
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
    Output('url-services', 'pathname', allow_duplicate=True),
    Output('input-new-service-type-name', 'value'),
    Input('save-new-service-type-btn', 'n_clicks'),
    State('input-new-service-type-name', 'value'),
    prevent_initial_call=True
)
def save_new_service_type(n_clicks, name):
    if n_clicks and name:
        success, message = add_service_type({'nome': name})
        
        if success:
            return '/dashboard/services', ''

    return dash.no_update, dash.no_update