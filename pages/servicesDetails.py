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

        html.Div([
            html.Div([
                html.H3(f"{dados.get('nomenclatura', 'N/A')}", className='tittle'),
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
                 html.Div([
                    html.A(id='pdf_serv_det_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf'),
            ], className='details-container card'),

            # The user requested to remove the other containers so the details can fill the screen.
        ], className='grid-details'),
    ], className='page-content details-page')

# The callback for the history table is no longer needed as the table has been removed.