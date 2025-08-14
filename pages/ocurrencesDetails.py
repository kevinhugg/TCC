import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime
import firebase_functions as fb

dash.register_page(__name__, path_template='/ocurrences/<id>', name=None)

def layout(id=None):
    dados = fb.get_occurrence_or_service_by_id(id)

    if not dados or dados.get('class') != 'ocorrencia':
        return html.Div([
            html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
            html.Div([
                html.Div("Ocorrência não encontrada ou inválida.", style={'textAlign': 'center', 'fontSize': '20px'}),
                html.Br(),
                html.A("Voltar para Ocorrências", href="/dashboard/ocurrences", className="btn btn-primary")
            ], style={'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '30px', 'boxShadow': '0 0 10px rgba(0,0,0,0.25)', 'textAlign': 'center', 'zIndex': 9999})
        ])

    vehicle_number = dados.get('viatura')
    vehicle_data = fb.get_vehicle_by_number(vehicle_number) if vehicle_number else None
    team_agents = fb.get_agents_by_vehicle(vehicle_number) if vehicle_number else []
    motorista = next((a for a in team_agents if a.get('funcao', '').lower() == 'motorista'), None)
    another_agents = [a for a in team_agents if a != motorista]

    history = fb.get_occurrences_and_services_by_vehicle(vehicle_number) if vehicle_number else []
    meses_unicos = sorted(list(set(datetime.strptime(h['data'], "%Y-%m-%d").strftime("%Y/%m") for h in history if h.get('class') == 'ocorrencia')))
    dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
        {'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(), 'value': m} for m in meses_unicos
    ]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='oc-store', data=id),
        dcc.Location(id='redirect-oco', refresh=True),

        # Deletion Modal
        html.Div(id='delete-modal-oco', className='modal', style={'display': 'none'}, children=[
            html.Div(className='modal-content', children=[
                html.Div(className='modal-header', children=[
                    html.H5('Confirmar Exclusão'),
                    html.Button('×', id='close-modal-oco', className='modal-close-button')
                ]),
                html.Div(className='modal-body', children=[
                    html.P("Você tem certeza que deseja excluir esta ocorrência?")
                ]),
                html.Div(className='modal-footer', children=[
                    html.Button('Cancelar', id='cancel-delete-oco', className='btn btn-secondary'),
                    html.Button('Excluir', id='confirm-delete-oco', className='btn btn-danger')
                ])
            ])
        ]),

        html.Div([
            html.H3(f"{dados.get('nomenclatura', 'N/A')}", className='tittle'),
            html.Div([
                html.Div([
                    html.P(f"Descrição: {dados.get('descricao', 'Não informada.')}"),
                    html.P(f"Endereço: {dados.get('endereco', 'Não informado.')}"),
                    html.P(f"Cidadão atendido: {dados.get('n_cidadao', 'Não informado.')}"),
                    html.P(f"Contato do cidadão: {dados.get('contato', 'Não informado.')}"),
                    dcc.Link(
                        html.P(f"Veículo: {dados.get('viatura', 'N/A')}"),
                        href=f"/dashboard/veiculo/{vehicle_data.get('numero')}" if vehicle_data else '#',
                        className='link-ag-vt'
                    )
                ], className='texts-det'),
            ], className='details-items'),
            html.Div([
                html.Div([
                    html.A(id='del_oco', children='Remover Ocorrência', className='btn rem_vehicle')
                ], className='btn_rem'),
                html.Div([
                    html.A(id='pdf_oco_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf'),
            ], className='btn_rem_pdf'),
        ], className='details-container'),

        html.Div([
            html.H4(f"Histórico de Ocorrências do Veículo {dados.get('viatura', '')}"),
            dcc.Dropdown(
                id='filter-month-oco',
                options=dropdown_options,
                value='todos',
                placeholder="Filtrar por mês...",
                className='filter-month'
            ),
            html.Div(id='table-oco-viat'),
        ], className='ocurrences'),

        html.Div([
            html.H3(f"Equipe Responsável"),
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=motorista.get('foto_agnt', '/static/img/default-user.png'), className='img'),
                        html.P(motorista.get('nome', 'N/A')),
                        html.P(f"Função: {motorista.get('funcao', 'N/A').capitalize()}"),
                    ], className='agent-box motorista'),
                    href=f"/dashboard/agent/{motorista.get('id')}"
                ) if motorista else html.Div("Sem motorista designado", className='agent-box'),

                *[dcc.Link(
                    html.Div([
                        html.Img(src=agente.get('foto_agnt', '/static/img/default-user.png'), className='img'),
                        html.P(agente.get('nome', 'N/A')),
                        html.P(f"Função: {agente.get('funcao', 'N/A').capitalize()}"),
                    ], className='agent-box'),
                    href=f"/dashboard/agent/{agente.get('id')}"
                ) for agente in another_agents]
            ], className='agents-grid'),
        ], className='agents-container'),
    ], className='page-content')

@callback(
    Output('table-oco-viat', 'children'),
    [Input('filter-month-oco', 'value'),
     Input('oc-store', 'data')]
)
def update_history_table_oco(selected_month, occurrence_id):
    occurrence = fb.get_occurrence_or_service_by_id(occurrence_id)
    if not occurrence:
        return html.P("Ocorrência não encontrada.")

    vehicle_number = occurrence.get('viatura')
    if not vehicle_number:
        return html.P("Viatura não especificada.")

    history = fb.get_occurrences_and_services_by_vehicle(vehicle_number)
    # Filter for occurrences only
    history = [h for h in history if h.get('class') == 'ocorrencia']

    if selected_month != 'todos':
        history = [h for h in history if datetime.strptime(h['data'], '%Y-%m-%d').strftime('%Y/%m') == selected_month]

    if not history:
        return html.P("Nenhum registro encontrado para este período.")

    table_header = [html.Thead(html.Tr([html.Th("Data"), html.Th("Tipo"), html.Th("Descrição")]))]
    table_body = [html.Tbody([
        html.Tr([
            html.Td(item['data']),
            html.Td(item['tipo']),
            html.Td(item['nomenclatura']),
            html.Td(dcc.Link('Ver Mais', href=f"/dashboard/ocurrences/{item['id']}", className="btn_view"))
        ]) for item in history
    ])]
    return html.Table(table_header + table_body, className='table-ocurrences-serv')

@callback(
    Output('delete-modal-oco', 'style'),
    [Input('del_oco', 'n_clicks'),
     Input('close-modal-oco', 'n_clicks'),
     Input('cancel-delete-oco', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_delete_modal_oco(n_open, n_close, n_cancel):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'del_oco':
        return {'display': 'block'}

    return {'display': 'none'}

@callback(
    Output('redirect-oco', 'pathname'),
    Input('confirm-delete-oco', 'n_clicks'),
    State('oc-store', 'data'),
    prevent_initial_call=True
)
def handle_delete_oco(n_clicks, occurrence_id):
    if n_clicks and occurrence_id:
        fb.delete_occurrence_or_service(occurrence_id)
        return '/dashboard/ocurrences'
    return dash.no_update