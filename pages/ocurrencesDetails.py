import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime
from data.dados import Ocur_Vehicles, viaturas, agents

dash.register_page(__name__, path_template='/ocurrences/<id>', name=None)

def layout(id=None):
    # Find the occurrence by ID from the local data
    dados = next((item for item in Ocur_Vehicles if item.get('id') == id), None)

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
    # Find vehicle data from local viaturas list
    vehicle_data = next((v for v in viaturas if v.get('numero') == vehicle_number), None)
    # Find team agents from local agents list
    team_agents = [a for a in agents if a.get('viatura_mes') == vehicle_number]
    # Note: 'funcao' in dados.py is 'func_mes'
    motorista = next((a for a in team_agents if a.get('func_mes', '').lower() == 'motorista'), None)
    another_agents = [a for a in team_agents if a != motorista]

    # Get history for the vehicle from local data
    history = [h for h in Ocur_Vehicles if h.get('viatura') == vehicle_number]
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

        # The user requested to remove the other containers so the details can fill the screen.
        # Removing agents-container and ocurrences (history) container.
    ], className='page-content details-page')

# The callback for the history table is no longer needed as the table has been removed.

# @callback(
#     Output('delete-modal-oco', 'style'),
#     [Input('del_oco', 'n_clicks'),
#      Input('close-modal-oco', 'n_clicks'),
#      Input('cancel-delete-oco', 'n_clicks')],
#     prevent_initial_call=True
# )
# def toggle_delete_modal_oco(n_open, n_close, n_cancel):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return {'display': 'none'}
#
#     trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
#     if trigger_id == 'del_oco':
#         return {'display': 'block'}
#
#     return {'display': 'none'}

# @callback(
#     Output('redirect-oco', 'pathname'),
#     Input('confirm-delete-oco', 'n_clicks'),
#     State('oc-store', 'data'),
#     prevent_initial_call=True
# )
# def handle_delete_oco(n_clicks, occurrence_id):
#     if n_clicks and occurrence_id:
#         # Logic to delete from data/dados.py would be needed here
#         print(f"Deletion of {occurrence_id} is not implemented in this version.")
#         return '/dashboard/ocurrences'
#     return dash.no_update