import dash
from dash import html, dcc, Input, Output, callback, ctx, State
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd
import dash_bootstrap_components as dbc

from data.dados import agents, Ocur_Vehicles

dash.register_page(__name__, path='/services', name='Serviços', className='pg-at')

item = next((v for v in Ocur_Vehicles))
servicos = [o for o in Ocur_Vehicles if o.get('class') == 'serviço']

responsavel = next((a['nome'] for a in agents if a['viatura_mes'] == item['viatura']), 'Desconhecido')
respon_id = next((a['id'] for a in agents if a['viatura_mes'] == item['viatura']), 'Desconhecido')
viat_func = next((a['viatura_mes'] for a in agents))

meses_unicos = sorted(set(
    datetime.strptime(o['data'], "%Y-%m-%d").strftime("%Y/%m")
    for o in Ocur_Vehicles if o['viatura'] == viat_func
))

dropdown_options = [{'label': 'Todos os meses', 'value': 'todos'}] + [
    {
        'label': datetime.strptime(m, "%Y/%m").strftime("%B/%Y").capitalize(),
        'value': m
    } for m in meses_unicos
]

#grafico ocorrencias registradas e seus dados
tipos = [item['nomenclatura'].strip() for item in servicos]
contagem_tipos = Counter(tipos)

tipos_labels = list(contagem_tipos.keys())
tipos_values = list(contagem_tipos.values())

df_tipos = pd.DataFrame({
    'Tipo': tipos_labels,
    'Quantidade': tipos_values
})

fig_tipos = px.bar(
    df_tipos,
    x='Tipo',
    y='Quantidade',
    text='Quantidade',
    labels={'Tipo': '', 'Quantidade': ''},
    title='Serviços Cadastrados'
)

fig_tipos.update_traces(marker_color='#f7e57d', textposition='outside')
fig_tipos.update_layout(
    title={
        'text': 'Serviços Cadastrados',
    },
    title_font_size=26,
    title_font_color='black',
)

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleOcurrencesServices.css'),

    dcc.Store(id='filtro-search'),

    html.Div([

        html.Div([

            html.Div([
                html.H3('Serviços Gerais', className='title'),
                dcc.Input(id='input-search', type='text', placeholder='Buscar por responsável ou viatura...', className='input-search'),
                dcc.Dropdown(
                    id='filter-month',
                    options=dropdown_options,
                    value='todos',
                    placeholder="Filtrar por mês...",
                    className='filter-month'
                ),
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
                html.Tbody(id='serv-table', children=[
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
                            dcc.Link('Ver Mais', href=f"/dashboard/services/{item['id']}"), className='btn_view'
                        ),
                    ])
                    for item in servicos
                ], className='sla')
            ], className='serv-table'),



            html.Div([
                html.Div([
                    html.A(id='rem_serv', children='Apagar Serviços', className='rem_serv')
                ], className='btn'),

                html.Div([
                   html.A(id='pdf_serv_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf-serv'),
            ], className='btn_rem_add_pdf'),

        ], className='oco_serv_container card'),
    ]),

    html.Div([
        dcc.Graph(figure=fig_tipos, className='fig_serv'),

        html.Div([
            html.Div([
                html.A(id='rem_vehicle_serv', children='Remover Serviço', className='rem_serv')
            ], className='btn'),

            html.Div([
                html.A(id='btn_add', children='Adicionar Serviço', className='btn_add')
            ], className='btn'),
        ], className='btn_rem_add_pdf'),

    ], className='graph_tipes card'),

    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle('Novo Serviço')),
            dbc.ModalBody([
                dbc.Input(id='input-tipo', placeholder='Digite o novo tipo...', type='text'),
            ]),
            dbc.ModalFooter([
                dbc.Button('Adicionar', id='btn-add-confirm', className='btn-confirm', n_clicks=0),
                dbc.Button('Cancelar', id='btn-cancel', className='btn-cancel', n_clicks=0),
            ]),
        ],
        id='modal-add',
        is_open=False,
    )

], className='page-content')

def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower()

@callback(
    Output('serv-table', 'children'),
    Output('pdf_serv_gerar', 'href'),
    Input('input-search', 'value'),
    Input('filter-month', 'value')
)
def update_list(search_value, mes):
    if not search_value:
        filtered = servicos
    else:
        search_value = remover_acentos(search_value.lower())
        filtered = [
            item for item in servicos
            if search_value in remover_acentos(item['viatura'].lower()) or
               any(search_value in remover_acentos(a['nome'].lower()) for a in agents if a['viatura_mes'] == item['viatura'])
        ]

    if mes != 'todos':
        filtered = [
            item for item in filtered
            if datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m') == mes
        ]

    if not filtered:
        return html.Tr([
            html.Td("Serviço não encontrado!", colSpan=5, className='not-found'),
        ]), f"/gerar_pdf_servicos_gerais?filtro={search_value}"

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
                    dcc.Link('Ver Mais', href=f"/dashboard/services/{item['id']}"), className='btn_view'
                ),
        ], className='sla')
        rows.append(row)

    pdf_link = f"/gerar_pdf_servicos_gerais?filtro={search_value or ''}&mes={mes}"

    return rows, pdf_link

@callback(
    Output('modal-add', 'is_open'),
    Input('btn_add', 'n_clicks'),
    Input('btn-cancel', 'n_clicks'),
    Input('btn-add-confirm', 'n_clicks'),
    State('modal-add', 'is_open'),
    prevent_initial_call=True
)
def toggle_modal(n_add, n_cancel, n_confirm, is_open):
    trigger = ctx.triggered_id
    if trigger in ['btn_add', 'btn-cancel', 'btn-add-confirm']:
        return not is_open
    return is_open

@callback(
    Output('fig_serv', 'figure'),
    Output('input-tipo', 'value'),
    Input('btn-add-confirm', 'n_clicks'),
    State('input-tipo', 'value'),
    prevent_initial_call='initial_duplicate'
)
def adicionar_tipo(n_clicks, novo_tipo):
    if not novo_tipo:
        raise dash.exceptions.PreventUpdate

    novo_tipo = novo_tipo.strip().capitalize()
    if novo_tipo and novo_tipo not in tipos:
        tipos.append(novo_tipo)
        tipos.sort()
    return [{'label': t, 'value': t} for t in tipos], ""
