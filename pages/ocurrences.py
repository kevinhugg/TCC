import dash
from dash import html, dcc, Input, Output, callback, State, ctx
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd
import dash_bootstrap_components as dbc
import firebase_functions as fb

dash.register_page(__name__, path='/ocurrences', name='Ocorrências', className='pg-at')


def remover_acentos(txt):
    if not txt:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def get_page_data():
    """Fetches and prepares all data needed for the occurrences page."""
    try:
        all_items = fb.get_all_occurrences_and_services()
        all_agents = fb.get_all_agents()

        # Filter for occurrences only
        ocorrencias = [o for o in all_items if o.get('class') == 'ocorrencia']

        # Create a mapping from vehicle number to responsible agent for efficient lookup
        agent_map = {}
        for agent in all_agents:
            vehicle = agent.get('viatura')
            # Assuming 'Encarregado' or 'Motorista' are the primary responsible roles
            if vehicle and agent.get('funcao') in ['Encarregado', 'Motorista']:
                if vehicle not in agent_map:  # Prioritize first responsible agent found
                    agent_map[vehicle] = {'nome': agent.get('nome'), 'id': agent.get('id')}

        return ocorrencias, agent_map
    except Exception as e:
        print(f"Error fetching data for occurrences page: {e}")
        return [], {}


def layout():
    ocorrencias, _ = get_page_data()
    vehicles = fb.get_all_vehicles()
    vehicle_options = [{'label': v['numero'], 'value': v['numero']} for v in vehicles] if vehicles else []

    # Generate month dropdown options from the fetched data
    if ocorrencias:
        meses_unicos = sorted(list(set(
            datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
            for o in ocorrencias
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
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Location(id='url-occurrences', refresh=True),

        # Modal for adding a new occurrence
        dbc.Modal([
            dbc.ModalHeader("Adicionar Nova Ocorrência"),
            dbc.ModalBody([
                dbc.Label("Data da Ocorrência:"),
                dcc.DatePickerSingle(
                    id='occurrence-date-picker',
                    display_format='DD/MM/YYYY',
                    className='date-picker'
                ),
                dbc.Label("Tipo de Ocorrência:", className="mt-3"),
                dbc.Input(id='occurrence-type-input', placeholder="Ex: Atendimento ao Cidadão"),
                dbc.Label("Viatura Responsável:", className="mt-3"),
                dcc.Dropdown(id='occurrence-vehicle-dropdown', options=vehicle_options,
                             placeholder="Selecione a viatura"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="cancel-add-occurrence", color="secondary"),
                dbc.Button("Salvar", id="save-new-occurrence", color="primary"),
            ]),
        ], id='modal-add-occurrence', is_open=False),

        html.Div([
            html.Div([
                html.Div([
                    html.H3('Ocorrências Gerais', className='title'),
                    dcc.Dropdown(
                        id='filter-month-oco',
                        options=dropdown_options,
                        value='todos',
                        placeholder="Filtrar por mês...",
                        className='filter-month'
                    ),
                    dcc.Input(id='input-search-oco', type='text', placeholder='Buscar por tipo ou viatura...',
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
                    html.Tbody(id='oco-table')
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
            dcc.Graph(id='fig_oco_tipos', className='fig_oco'),
            html.Div([
                html.Div([
                    html.A(id='add_oco', children='Adicionar Ocorrência', className='btn_add')
                ], className='btn'),
            ], className='btn_rem_add_pdf'),
        ], className='graph_tipes'),

    ], className='page-content')


@callback(
    Output('oco-table', 'children'),
    Output('pdf_oco_gerar', 'href'),
    Input('input-search-oco', 'value'),
    Input('filter-month-oco', 'value'),
)
def update_list(search_value, mes):
    ocorrencias, agent_map = get_page_data()

    if not ocorrencias:
        return html.Tr([
            html.Td("Nenhuma ocorrência encontrada.", colSpan=5, className='not-found'),
        ]), "/gerar_pdf_ocorrencias"

    if mes != 'todos':
        filtered = [
            item for item in ocorrencias
            if datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]
    else:
        filtered = ocorrencias

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
            html.Td("Ocorrência não encontrada!", colSpan=5, className='not-found'),
        ]), f"/gerar_pdf_ocorrencias?filtro={search_value}&mes={mes}"

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
                dcc.Link('Ver Mais', href=f"/dashboard/ocurrences/{item.get('id', '')}"), className='btn_view'
            ),
        ])
        rows.append(row)

    pdf_link = f"/gerar_pdf_ocorrencias?filtro={search_value or ''}&mes={mes}"

    return rows, pdf_link


@callback(
    Output('fig_oco_tipos', 'figure'),
    Input('filter-month-oco', 'value'),
    Input('theme-mode', 'data')
)
def update_graph(mes, theme):
    ocorrencias, _ = get_page_data()

    if not ocorrencias:
        return px.bar(title='Nenhuma Ocorrência Cadastrada')

    if mes != 'todos':
        filtered = [
            item for item in ocorrencias
            if datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]
    else:
        filtered = ocorrencias

    tipos = [item['nomenclatura'].strip() for item in filtered]
    contagem_tipos = Counter(tipos)

    if not contagem_tipos:
        return px.bar(title=f'Nenhuma ocorrência em {mes}')

    df_ocorrencias = pd.DataFrame({
        'Tipo': list(contagem_tipos.keys()),
        'Quantidade': list(contagem_tipos.values())
    })

    is_dark = theme == 'dark'
    bar_color = '#60a5fa' if is_dark else '#4682B4'
    title_color = '#f9fafb' if is_dark else '#295678'
    bg_color = 'rgba(0,0,0,0)'

    fig_tipos = px.bar(
        df_ocorrencias,
        x='Tipo',
        y='Quantidade',
        text='Quantidade',
        labels={'Tipo': '', 'Quantidade': ''},
        title='Ocorrências Cadastradas'
    )

    fig_tipos.update_traces(marker_color=bar_color, textposition='outside')
    fig_tipos.update_layout(
        title={'text': 'Ocorrências Cadastradas'},
        title_font_size=26,
        title_font_color=title_color,
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font_color=title_color
    )

    return fig_tipos


@callback(
    Output('modal-add-occurrence', 'is_open'),
    Input('add_oco', 'n_clicks'),
    Input('cancel-add-occurrence', 'n_clicks'),
    State('modal-add-occurrence', 'is_open'),
    prevent_initial_call=True,
)
def toggle_modal_occurrence(n_add, n_cancel, is_open):
    if ctx.triggered_id in ['add_oco', 'cancel-add-occurrence']:
        return not is_open
    return is_open


@callback(
    Output('url-occurrences', 'pathname', allow_duplicate=True),
    Output('modal-add-occurrence', 'is_open', allow_duplicate=True),
    Input('save-new-occurrence', 'n_clicks'),
    State('occurrence-date-picker', 'date'),
    State('occurrence-type-input', 'value'),
    State('occurrence-vehicle-dropdown', 'value'),
    prevent_initial_call=True,
)
def save_new_occurrence(n_clicks, date, occ_type, vehicle):
    if n_clicks:
        if not all([date, occ_type, vehicle]):
            return dash.no_update, True

        agents = fb.get_agents_by_vehicle(vehicle)
        if not agents:
            print(f"No agent found for vehicle {vehicle}")
            return dash.no_update, True

        agent_id = agents[0].get('id')
        if not agent_id:
            print("Agent found but has no ID")
            return dash.no_update, True

        occ_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
        occ_data = {
            'nomenclatura': occ_type,
            'viatura': vehicle,
            'class': 'ocorrencia'
        }

        fb.add_occurrence(agent_id, occ_date, occ_data)

        return '/ocurrences', False

    return dash.no_update, True