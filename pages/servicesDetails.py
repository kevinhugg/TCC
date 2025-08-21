import dash
from dash import html, dcc, Input, Output, callback
from datetime import datetime
from data.dados import Ocur_Vehicles, viaturas, agents

dash.register_page(__name__, path_template='/services/<id>', name=None)

def layout(id=None):
    # Find the service by ID from the local data
    dados = next((item for item in Ocur_Vehicles if item.get('id') == id), None)

    if not dados or dados.get('class') != 'serviço':
        return html.Div([
            html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
            html.Div([
                html.Div("Serviço não encontrado ou inválido.", style={'textAlign': 'center', 'fontSize': '20px'}),
                html.Br(),
                html.A("Voltar para Serviços", href="/dashboard/services", className="btn btn-primary")
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
    meses_unicos = sorted(list(set(datetime.strptime(h['data'], "%Y-%m-%d").strftime("%Y/%m") for h in history if h.get('class') == 'serviço')))
    dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
        {'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(), 'value': m} for m in meses_unicos
    ]

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='serv-store', data=id),
        dcc.Location(id='redirect-serv', refresh=True),

        # Deletion Modal REMOVED

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
                # REMOVED Delete button
                html.Div([
                    html.A(id='pdf_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf'),
            ], className='btn_rem_pdf'),
        ], className='details-container'),

        html.Div([
            html.H4(f"Histórico de Serviços do Veículo {dados.get('viatura', '')}"),
            dcc.Dropdown(
                id='filter-month-serv',
                options=dropdown_options,
                value='todos',
                placeholder="Filtrar por mês...",
                className='filter-month'
            ),
            html.Div(id='table-serv-viat'),
        ], className='services'),

        html.Div([
            html.H3(f"Equipe Responsável"),
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=motorista.get('foto_agnt', '/static/img/default-user.png'), className='img'),
                        html.P(motorista.get('nome', 'N/A')),
                        html.P(f"Função: {motorista.get('func_mes', 'N/A').capitalize()}"),
                    ], className='agent-box motorista'),
                    href=f"/dashboard/agent/{motorista.get('id')}"
                ) if motorista else html.Div("Sem motorista designado", className='agent-box'),

                *[dcc.Link(
                    html.Div([
                        html.Img(src=agente.get('foto_agnt', '/static/img/default-user.png'), className='img'),
                        html.P(agente.get('nome', 'N/A')),
                        html.P(f"Função: {agente.get('func_mes', 'N/A').capitalize()}"),
                    ], className='agent-box'),
                    href=f"/dashboard/agent/{agente.get('id')}"
                ) for agente in another_agents]
            ], className='agents-grid'),
        ], className='agents-container'),
    ], className='page-content')

@callback(
    Output('table-serv-viat', 'children'),
    [Input('filter-month-serv', 'value'),
     Input('serv-store', 'data')]
)
def update_history_table_serv(selected_month, service_id):
    service = next((item for item in Ocur_Vehicles if item.get('id') == service_id), None)
    if not service:
        return html.P("Serviço não encontrado.")

    vehicle_number = service.get('viatura')
    if not vehicle_number:
        return html.P("Viatura não especificada.")

    # Get history and filter for services only
    history = [h for h in Ocur_Vehicles if h.get('viatura') == vehicle_number and h.get('class') == 'serviço']

    if selected_month != 'todos':
        history = [h for h in history if datetime.strptime(h['data'], '%Y-%m-%d').strftime('%Y/%m') == selected_month]

    if not history:
        return html.P("Nenhum registro encontrado para este período.")

    table_header = [html.Thead(html.Tr([html.Th("Data"), html.Th("Tipo"), html.Th("Descrição")]))]
    table_body = [html.Tbody([
        html.Tr([
            html.Td(item['data']),
            html.Td(item.get('class', 'serviço').capitalize()),
            html.Td(item['nomenclatura']),
            html.Td(dcc.Link('Ver Mais', href=f"/dashboard/services/{item['id']}", className="btn_view"))
        ]) for item in history
    ])]
    return html.Table(table_header + table_body, className='table-ocurrences-serv')