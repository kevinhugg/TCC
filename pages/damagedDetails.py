import dash
from dash import html, dcc, Input, Output, callback, State
import firebase_functions as fb

dash.register_page(__name__, path_template='/damage/<damage_id>', name=None)

def layout(damage_id=None):
    if not damage_id:
        return html.Div("ID do dano não fornecido.", className="error-message")

    damage_data = fb.get_damage_by_id(damage_id)

    if not damage_data:
        return html.Div([
            html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),
            html.Div([
                html.Div("Relatório de dano não encontrado.", style={'textAlign': 'center', 'fontSize': '20px'}),
                html.Br(),
                dcc.Link("Voltar", href="/dashboard/pageVehicles", className="btn btn-primary")
            ], className="not-found-container")
        ])

    vehicle_number = damage_data.get('viatura', '')

    return html.Div([
        html.Link(rel='stylesheet', href='https://use.fontawesome.com/releases/v5.8.1/css/all.css'),
        html.Link(rel='stylesheet', href='/static/css/detailsOcurrencesServices.css'),

        html.Div([
            html.Div([
                html.H3(f"Dano em: {damage_data.get('parte', 'N/A')}", className='tittle'),
                html.Div([
                    html.Div([
                        html.Img(
                            src=damage_data.get('uriFoto') if damage_data.get('uriFoto') else '/static/assets/img/imageNot.png',
                            className='damage-image'
                        )
                    ], className='damage-image-container'),

                    html.Div([
                        html.P(f"Área Danificada: {damage_data.get('parte', 'N/A')}"),
                        html.P(f"Descrição: {damage_data.get('descricao', 'Não informada.')}"),
                        html.P(f"Data do Registro: {damage_data.get('data', 'Não informada.')}"),
                        dcc.Link(
                            html.P(f"Viatura: {vehicle_number}"),
                            href=f"/dashboard/veiculo/{vehicle_number}" if vehicle_number else '#',
                            className='link-ag-vt'
                        )
                    ], className='damage-text-container')
                ], className='damage-content-wrapper'),

                html.Div([
                    html.Button('Apagar Dano', id='delete-damage-button', n_clicks=0, className='btn rem_vehicle')
                ], className='btn_rem_add')
            ], className='details-container card'),
        ], className='grid-details'),
        dcc.Location(id='delete-redirect-url', refresh=True),
        dcc.ConfirmDialog(
            id='confirm-delete-damage',
            message='Você tem certeza que quer apagar este registro de dano?',
        ),
        dcc.Store(id='damage-id-store', data=damage_id),
        dcc.Store(id='vehicle-number-store', data=vehicle_number)
    ], className='page-content details-page')

@callback(
    Output('confirm-delete-damage', 'displayed'),
    Input('delete-damage-button', 'n_clicks'),
    prevent_initial_call=True
)
def display_confirm(n_clicks):
    if n_clicks > 0:
        return True
    return False

@callback(
    Output('delete-redirect-url', 'pathname'),
    Input('confirm-delete-damage', 'submit_n_clicks'),
    State('damage-id-store', 'data'),
    State('vehicle-number-store', 'data'),
    prevent_initial_call=True
)
def delete_damage(submit_n_clicks, damage_id, vehicle_number):
    if submit_n_clicks:
        if fb.delete_damage_by_id(damage_id):
            return f"/dashboard/veiculo/{vehicle_number}"
    return dash.no_update