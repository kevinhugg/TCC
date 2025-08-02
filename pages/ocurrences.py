import dash
from dash import html, dcc, Input, Output, callback
import unicodedata
from collections import Counter
import plotly.express as px
from datetime import datetime
import pandas as pd

from data.dados import agents, Ocur_Vehicles

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

#grafico ocorrencias registradas e seus dados
tipos = [item['nomenclatura'].strip() for item in ocorrencias]
contagem_tipos = Counter(tipos)

tipos_labels = list(contagem_tipos.keys())
tipos_values = list(contagem_tipos.values())

df_ocorrencias = pd.DataFrame({
    'Tipo': tipos_labels,
    'Quantidade': tipos_values
})

fig_tipos = px.bar(
    df_ocorrencias,
    x='Tipo',
    y='Quantidade',
    text='Quantidade',
    labels={'Tipo': '', 'Quantidade': ''},
    title='Ocorrências Cadastradas'
)

fig_tipos.update_traces(marker_color='#f7e57d', textposition='outside')
fig_tipos.update_layout(
    title={
        'text': 'Ocorrências Cadastradas',
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
                html.H3('Ocorrências Gerais', className='title'),
                dcc.Dropdown(
                    id='filter-month',
                    options=dropdown_options,
                    value='todos',
                    placeholder="Filtrar por mês...",
                    className='filter-month'
                ),
                dcc.Input(id='input-search', type='text', placeholder='Buscar por responsável ou viatura...', className='input-search'),
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
                    html.A(id='rem_oco', children='Apagar Ocorrências', className='rem_oco')
                ], className='btn'),

                html.Div([
                   html.A(id='pdf_oco_gerar', children='Gerar PDF', target="_blank", className='btn-pdf')
                ], className='btn-pdf-oco'),
            ], className='btn_rem_add_pdf'),

        ], className='oco_serv_container'),
    ]),

    html.Div([
        dcc.Graph(figure=fig_tipos, className='fig_oco'),

        html.Div([
            html.Div([
                html.A(id='rem_vehicle', children='Remover Ocorrência', className='rem_oco')
            ], className='btn'),

            html.Div([
                html.A(id='add_vehicle', children='Adicionar Ocorrência', className='btn_add')
            ], className='btn'),
        ], className='btn_rem_add_pdf'),

    ], className='graph_tipes'),

], className='page-content')

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
               any(search_value in remover_acentos(a['nome'].lower()) for a in agents if a['viatura_mes'] == item['viatura'])
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