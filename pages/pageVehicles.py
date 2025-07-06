from pydoc import classname

import dash
from dash import html, dcc, Input, Output, callback

dash.register_page(__name__, path='/pageVehicles', name='Veículos')

#para a lista das viaturas
viaturas = [
    {'id': 1, 'placa': 'ABC-1234', 'numero': 'V001', 'avariada': True, 'imagem': '/assets/viatura1.jpg'},
    {'id': 2, 'placa': 'DEF-5678', 'numero': 'V002', 'avariada': False, 'imagem': '/assets/viatura1.jpg'},
    {'id': 3, 'placa': 'GHI-9012', 'numero': 'V003', 'avariada': True, 'imagem': '/assets/viatura1.jpg'},
    {'id': 4, 'placa': 'JKL-3456', 'numero': 'V004', 'avariada': False, 'imagem': '/assets/viatura1.jpg'},
]

viaturas_sorted = sorted(viaturas, key=lambda x: not x['avariada'])

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleVehicles.css'),

    html.Div([
        html.H2('Viaturas', className='tittle'),
        html.Div([
            html.Div([
                html.Img(src=viaturas['imagem'], className='img-vehicle'),
                html.H4(f"Placa: {viaturas['placa']}"),
                html.P(f"Número: {viaturas['numero']}"),
                html.P(
                    f"Situação: {'Avariada' if viaturas['avariada'] else 'Operacional'}",
                    className='situation-ava' if viaturas['avariada'] else 'situation-op'
                )
            ], className='card-vehicles')
            for viaturas in viaturas_sorted
        ], className='list-vehicles')
        ])
    ], className='page-content'),  # AQUI precisa estar a grid