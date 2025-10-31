import dash
from dash import html, dcc, Input, Output, callback, State
import plotly.graph_objects as go
import plotly.express as px
import firebase_functions as fb
from datetime import datetime, timedelta
from collections import defaultdict, Counter

dash.register_page(__name__, path='/', name='Home')

def layout():
    try:
        all_vehicles = fb.get_all_vehicles()
        damage_reports = fb.get_all_damage_reports()
        vehiclesTot = len(all_vehicles)
        damaged_vehicle_numbers = {report['viatura'] for report in damage_reports}
        damagedVehic = len(damaged_vehicle_numbers)
        perfectVehic = vehiclesTot - damagedVehic
        
        all_services = fb.get_all_services_with_agents()
        current_month = datetime.now().strftime('%Y-%m')
        
        services_this_month = [
            service for service in all_services 
            if service.get('data', '').startswith(current_month)
        ]
        
        all_occurrences = fb.get_all_occurrences()
        occurrences_this_month = [
            occurrence for occurrence in all_occurrences 
            if occurrence.get('data', '').startswith(current_month)
        ]
        
    except Exception as e:
        damagedVehic, perfectVehic = 0, 0
        services_this_month = []
        occurrences_this_month = []

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/home.css'),
        html.Div([
            html.Div([
                html.H4('Viaturas'),
                html.Div([
                    html.Div([
                        html.H5('Com avarias:'),
                        html.P(damagedVehic, className='NumsVehicles'),
                    ], className='info-vehic'),
                    html.Div([
                        html.H5('Sem avarias:'),
                        html.P(perfectVehic, className='NumsVehicles'),
                    ], className='info-vehic')
                ], className='category'),
            ], className="vehicles card"),

            html.Div([
                html.H4('Agentes Logados'),
                html.Div([
                    html.Div(id='value-agents'),
                    html.Div(id='flux'),
                ], className='agents-info'),
                html.Div(
                    html.I(className="fas fa-info-circle", style={'color': '#6b7280', 'fontSize': '12px'}),
                    title="Agentes com viatura atribuída são considerados logados",
                    style={'position': 'absolute', 'top': '10px', 'right': '10px', 'cursor': 'help'}
                ),
                dcc.Interval(id='interval', interval=3000, n_intervals=0)
            ], className="agents card"),

            html.Div([
                html.H4('Serviços do Mês'),
                html.Div([
                    html.P(f'{len(services_this_month)}', className='NumServicesMonth', style={
                        'fontSize': '2.5rem',
                        'fontWeight': 'bold',
                        'color': '#3b82f6',
                        'textAlign': 'center',
                        'margin': '0'
                    }),
                    html.P('serviços realizados', style={
                        'textAlign': 'center',
                        'color': 'var(--secondary-text-color)',
                        'margin': '5px 0 0 0',
                        'fontSize': '0.9rem'
                    }),
                    html.P(f'{datetime.now().strftime("%B/%Y")}', style={
                        'textAlign': 'center',
                        'color': 'var(--secondary-text-color)',
                        'margin': '2px 0 0 0',
                        'fontSize': '0.8rem',
                        'fontStyle': 'italic'
                    })
                ], className='category', style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'justifyContent': 'center',
                    'alignItems': 'center',
                    'height': '100%'
                }),
            ], className="servicesMonth card"),

            html.Div([
                html.H4('Ocorrências no Mês'),
                html.Div([
                    html.P(f'{len(occurrences_this_month)}', className='NumOcuMonth'),
                    html.P(f'{datetime.now().strftime("%B/%Y")}', style={
                        'textAlign': 'center',
                        'color': 'var(--secondary-text-color)',
                        'margin': '2px 0 0 0',
                        'fontSize': '0.8rem',
                        'fontStyle': 'italic'
                    })
                ], className='category', style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'justifyContent': 'center',
                    'alignItems': 'center',
                    'height': '100%'
                }),
            ], className="ocuMonthly card"),

            html.Div([
                dcc.Graph(
                    id='bar-chart',
                    config={
                        'modeBarButtonsToRemove': [
                            'zoom2d', 'pan2d', 'select2d', 'lasso2d',
                            'autoScale2d', 'resetScale2d',
                            'zoomIn', 'zoomOut'
                        ],
                        'displaylogo': False
                    }
                )
            ], className="GraphIndOcu card"),

            html.Div([
                dcc.Dropdown(
                    id='dropdown-year',
                    options=[
                        {'label': 'Últimos 6 meses', 'value': '6months'},
                        {'label': 'Últimos 12 meses', 'value': '12months'}
                    ],
                    value='6months',
                    clearable=False,
                    style={'width': '150px'}
                ),
                dcc.Graph(
                    id='services-monthly-chart',
                    config={
                        'modeBarButtonsToRemove': [
                            'zoom2d', 'pan2d', 'select2d', 'lasso2d',
                            'autoScale2d', 'resetScale2d',
                            'zoomIn', 'zoomOut'
                        ],
                        'displaylogo': False
                    }
                ),
            ], className="GraphTimeRes card"),

            html.Div([
                html.H4('Ocorrências Mais Comuns'),
                html.Div(id='most-common-occurrences-table'),
            ], className="Ranking_Ocu card"),

            html.Div([
                html.H4('Distrubuição Geográfica das Ocorrências'),
                html.Div([
                    dcc.Graph(
                        id='map-chart',
                        config={
                            'displayModeBar': True,
                            'ScrollZoom': True,
                            'displaylogo': False
                        },
                    )
                ]),
            ], className='GraphMap card'),
            html.Div([
                html.H4('Bairros com mais ocorrências'),
                html.Div(id='neighborhoods-table'),
            ], className='NgbhInfos card'),
        ], className='page-content home-grid'),
    ])


@callback(
    Output('bar-chart', 'figure'),
    Output('map-chart', 'figure'),
    Output('most-common-occurrences-table', 'children'),
    Output('neighborhoods-table', 'children'),
    Output('services-monthly-chart', 'figure'),
    Input('theme-mode', 'data'),
    Input('dropdown-year', 'value')
)
def update_static_graphs(theme, time_range):
    # CORES DINÂMICAS BASEADAS NO TEMA
    if theme == 'dark':
        plot_bg_color = '#1f2937'
        paper_bg_color = '#1f2937'
        font_color = '#ffffff'
        grid_color = '#374151'
        marker_color = '#60a5fa'
        table_header_bg = '#374151'
        table_row_even = '#1f2937'
        table_row_odd = '#111827'
        map_style = 'carto-darkmatter'
    elif theme == 'high-contrast':
        plot_bg_color = '#000000'
        paper_bg_color = '#000000'
        font_color = '#ffffff'
        grid_color = '#ffff00'
        marker_color = '#ffff00'
        table_header_bg = '#000000'
        table_row_even = '#000000'
        table_row_odd = '#333333'
        map_style = 'carto-darkmatter'
    else:  # light mode
        plot_bg_color = '#ffffff'
        paper_bg_color = '#ffffff'
        font_color = '#1f2937'
        grid_color = '#e5e7eb'
        marker_color = '#3b82f6'
        table_header_bg = '#f9fafb'
        table_row_even = '#ffffff'
        table_row_odd = '#f8f9fa'
        map_style = 'open-street-map'

    def get_occurrence_location_data():
        try:
            all_occurrences = fb.get_all_occurrences()
            neighborhood_data = {}
            
            for occurrence in all_occurrences:
                bairro = (occurrence.get('bairro') or 
                         occurrence.get('local') or 
                         occurrence.get('endereco') or 
                         'Não especificado')
                
                latitude = (occurrence.get('latitude') or 
                           occurrence.get('lat') or 
                           occurrence.get('localizacao_lat'))
                longitude = (occurrence.get('longitude') or 
                            occurrence.get('lon') or 
                            occurrence.get('lng') or 
                            occurrence.get('localizacao_lng'))
                
                if not latitude or not longitude:
                    endereco_completo = occurrence.get('endereco_completo') or occurrence.get('localizacao') or ''
                    if ',' in endereco_completo:
                        try:
                            coords = [coord.strip() for coord in endereco_completo.split(',')]
                            if len(coords) >= 2:
                                lat_candidate = float(coords[0])
                                lng_candidate = float(coords[1])
                                if -90 <= lat_candidate <= 90 and -180 <= lng_candidate <= 180:
                                    latitude, longitude = lat_candidate, lng_candidate
                        except (ValueError, IndexError):
                            pass
                
                if not latitude or not longitude:
                    latitude, longitude = -23.511, -46.876
                
                try:
                    latitude = float(latitude)
                    longitude = float(longitude)
                except (ValueError, TypeError):
                    latitude, longitude = -23.511, -46.876
                
                if bairro and bairro != 'Não especificado':
                    if bairro not in neighborhood_data:
                        neighborhood_data[bairro] = {
                            'quantidade': 0,
                            'latitude': latitude,
                            'longitude': longitude
                        }
                    neighborhood_data[bairro]['quantidade'] += 1
            
            return neighborhood_data
            
        except Exception as e:
            return {}

    try:
        all_occurrences = fb.get_all_occurrences()
        current_date = datetime.now()
        monthly_occurrences = defaultdict(int)
        
        for occurrence in all_occurrences:
            if occurrence.get('data'):
                try:
                    occurrence_date = datetime.strptime(occurrence['data'], '%Y-%m-%d')
                    six_months_ago = current_date.replace(day=1)
                    for _ in range(5):
                        six_months_ago = (six_months_ago.replace(day=1) - timedelta(days=1)).replace(day=1)
                    
                    if occurrence_date >= six_months_ago:
                        month_key = occurrence_date.strftime('%Y-%m')
                        monthly_occurrences[month_key] += 1
                except Exception as e:
                    continue
        
        last_6_months = []
        for i in range(5, -1, -1):
            month = (current_date.replace(day=1) - timedelta(days=30*i)).strftime('%Y-%m')
            last_6_months.append(month)
        
        month_names = []
        occurrence_counts = []
        
        for month in last_6_months:
            month_date = datetime.strptime(month, '%Y-%m')
            month_names.append(month_date.strftime('%b/%y'))
            occurrence_counts.append(monthly_occurrences.get(month, 0))
        
        graphOcurrence = go.Figure(
            data=[go.Bar(
                x=month_names, 
                y=occurrence_counts, 
                marker=dict(color=marker_color),
                hovertemplate='<b>%{x}</b><br>Ocorrências: %{y}<extra></extra>'
            )]
        )
        
        graphOcurrence.update_layout(
            plot_bgcolor=plot_bg_color,
            paper_bgcolor=paper_bg_color,
            title={"text": "Ocorrências por Mês", "x": 0.5, "xanchor": "center", "font": {"color": font_color, "size": 14}},
            margin=dict(t=40, b=30, l=40, r=20),
            font=dict(color=font_color),
            xaxis=dict(
                title='Mês',
                title_font=dict(color=font_color),
                tickfont=dict(color=font_color),
                gridcolor=grid_color,
                linecolor=grid_color,
                zerolinecolor=grid_color
            ),
            yaxis=dict(
                title='Número de Ocorrências',
                title_font=dict(color=font_color),
                tickfont=dict(color=font_color),
                gridcolor=grid_color,
                linecolor=grid_color,
                zerolinecolor=grid_color
            )
        )
        
    except Exception as e:
        graphOcurrence = go.Figure(
            data=[go.Bar(x=['Jan', 'Fev', 'Mar', 'Abr', 'Mai'], y=[10, 20, 30, 15, 45], marker=dict(color=marker_color))]
        )
        graphOcurrence.update_layout(
            plot_bgcolor=plot_bg_color,
            paper_bgcolor=paper_bg_color,
            title={"text": "Ocorrências por Mês", "x": 0.5, "xanchor": "center", "font": {"color": font_color}},
            margin=dict(t=40, b=30, l=30, r=30),
            font=dict(color=font_color)
        )

    try:
        neighborhood_data = get_occurrence_location_data()
        
        neighborhoods_list = []
        for bairro, data in neighborhood_data.items():
            neighborhoods_list.append({
                'bairro': bairro,
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'quantidade': data['quantidade']
            })
        
        top_neighborhoods = sorted(neighborhoods_list, key=lambda x: x['quantidade'], reverse=True)[:15]
        
        if top_neighborhoods:
            GraphMapOcurrence = go.Figure()
            
            GraphMapOcurrence.add_trace(go.Scattermapbox(
                lat=[b['latitude'] for b in top_neighborhoods],
                lon=[b['longitude'] for b in top_neighborhoods],
                mode='markers',
                marker=dict(
                    size=[min(b['quantidade'] * 3 + 8, 25) for b in top_neighborhoods],
                    color=marker_color,
                    opacity=0.8,
                    sizemode='diameter'
                ),
                text=[f"{b['bairro']}<br>Ocorrências: {b['quantidade']}" for b in top_neighborhoods],
                hovertemplate='<b>%{text}</b><extra></extra>',
                name='Ocorrências'
            ))
            
            GraphMapOcurrence.update_layout(
                mapbox=dict(
                    style=map_style,
                    center=dict(lat=-23.505, lon=-46.875),
                    zoom=13.5,
                ),
                margin=dict(t=0, b=0, l=0, r=0),
                height=300,
                showlegend=False,
                paper_bgcolor=paper_bg_color,
                plot_bgcolor=plot_bg_color,
                font=dict(color=font_color)
            )
            
        else:
            GraphMapOcurrence = go.Figure()
            GraphMapOcurrence.update_layout(
                mapbox=dict(
                    style=map_style, 
                    center=dict(lat=-23.511, lon=-46.876), 
                    zoom=12
                ),
                margin=dict(t=0, b=0, l=0, r=0),
                height=300,
                paper_bgcolor=paper_bg_color,
                plot_bgcolor=plot_bg_color,
                annotations=[dict(
                    text="Nenhum dado de localização disponível",
                    x=0.5, y=0.5, xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(color=font_color, size=12)
                )]
            )
            
    except Exception as e:
        GraphMapOcurrence = go.Figure()
        GraphMapOcurrence.update_layout(
            mapbox=dict(
                style=map_style, 
                center=dict(lat=-23.511, lon=-46.876), 
                zoom=12
            ),
            margin=dict(t=0, b=0, l=0, r=0),
            height=300,
            paper_bgcolor=paper_bg_color,
            plot_bgcolor=plot_bg_color,
            annotations=[dict(
                text="Erro ao carregar mapa",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False,
                font=dict(color=font_color, size=12)
            )]
        )

    try:
        all_occurrences = fb.get_all_occurrences()
        occurrence_types = []
        for occurrence in all_occurrences:
            tipo_ocorrencia = occurrence.get('tipo_ocorrencia', 'Não especificado')
            if tipo_ocorrencia and tipo_ocorrencia != 'Não especificado':
                occurrence_types.append(tipo_ocorrencia)
        
        type_counter = Counter(occurrence_types)
        most_common_types = type_counter.most_common(5)
        
        if most_common_types:
            most_common_table = html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Tipo de Ocorrência', style={
                            'backgroundColor': table_header_bg,
                            'padding': '10px',
                            'textAlign': 'left',
                            'fontWeight': 'bold',
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        }),
                        html.Th('Quantidade', style={
                            'backgroundColor': table_header_bg,
                            'padding': '10px',
                            'textAlign': 'center',
                            'fontWeight': 'bold',
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        })
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(tipo, style={
                            'padding': '8px 10px',
                            'borderBottom': f'1px solid {grid_color}',
                            'backgroundColor': table_row_even if i % 2 == 0 else table_row_odd,
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        }),
                        html.Td(quantidade, style={
                            'padding': '8px 10px',
                            'borderBottom': f'1px solid {grid_color}',
                            'textAlign': 'center',
                            'fontWeight': 'bold',
                            'backgroundColor': table_row_even if i % 2 == 0 else table_row_odd,
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        })
                    ]) for i, (tipo, quantidade) in enumerate(most_common_types)
                ])
            ], className='table_ocu', style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'fontSize': '14px',
                'border': f'1px solid {grid_color}'
            })
        else:
            most_common_table = html.Div(
                "Nenhuma ocorrência encontrada",
                style={
                    'textAlign': 'center',
                    'padding': '20px',
                    'color': font_color,
                    'fontStyle': 'italic'
                }
            )
            
    except Exception as e:
        most_common_table = html.Div(
            "Erro ao carregar dados",
            style={
                'textAlign': 'center',
                'padding': '20px',
                'color': '#ef4444',
                'fontStyle': 'italic'
            }
        )

    try:
        neighborhood_data = get_occurrence_location_data()
        neighborhoods_data = [
            {'bairro': bairro, 'quantidade': data['quantidade']} 
            for bairro, data in neighborhood_data.items()
        ]
        neighborhoods_data = sorted(neighborhoods_data, key=lambda x: x['quantidade'], reverse=True)[:8]
        
        if neighborhoods_data:
            neighborhoods_table = html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Bairro', style={
                            'backgroundColor': table_header_bg,
                            'padding': '10px',
                            'textAlign': 'left',
                            'fontWeight': 'bold',
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        }),
                        html.Th('Ocorrências', style={
                            'backgroundColor': table_header_bg,
                            'padding': '10px',
                            'textAlign': 'center',
                            'fontWeight': 'bold',
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        })
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(bairro['bairro'], style={
                            'padding': '8px 10px',
                            'borderBottom': f'1px solid {grid_color}',
                            'backgroundColor': table_row_even if i % 2 == 0 else table_row_odd,
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        }),
                        html.Td(bairro['quantidade'], style={
                            'padding': '8px 10px',
                            'borderBottom': f'1px solid {grid_color}',
                            'textAlign': 'center',
                            'fontWeight': 'bold',
                            'backgroundColor': table_row_even if i % 2 == 0 else table_row_odd,
                            'color': font_color,
                            'border': f'1px solid {grid_color}'
                        })
                    ]) for i, bairro in enumerate(neighborhoods_data)
                ])
            ], className='table_neighborhoods', style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'fontSize': '14px',
                'border': f'1px solid {grid_color}'
            })
        else:
            neighborhoods_table = html.Div(
                "Nenhum dado de bairro disponível",
                style={
                    'textAlign': 'center',
                    'padding': '20px',
                    'color': font_color,
                    'fontStyle': 'italic'
                }
            )
            
    except Exception as e:
        neighborhoods_table = html.Div(
            "Erro ao carregar dados dos bairros",
            style={
                'textAlign': 'center',
                'padding': '20px',
                'color': '#ef4444',
                'fontStyle': 'italic'
            }
        )

    try:
        all_services = fb.get_all_services_with_agents()
        
        current_date = datetime.now()
        if time_range == '12months':
            months_range = 12
        else:
            months_range = 6
        
        monthly_services = defaultdict(int)
        
        for service in all_services:
            if service.get('data'):
                try:
                    service_date = datetime.strptime(service['data'], '%Y-%m-%d')
                    
                    start_date = current_date.replace(day=1)
                    for _ in range(months_range - 1):
                        start_date = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
                    
                    if service_date >= start_date:
                        month_key = service_date.strftime('%Y-%m')
                        monthly_services[month_key] += 1
                        
                except Exception as e:
                    continue
        
        months_list = []
        for i in range(months_range - 1, -1, -1):
            month = (current_date.replace(day=1) - timedelta(days=30*i)).strftime('%Y-%m')
            months_list.append(month)
        
        month_names = []
        service_counts = []
        
        for month in months_list:
            month_date = datetime.strptime(month, '%Y-%m')
            month_names.append(month_date.strftime('%b/%y'))
            service_counts.append(monthly_services.get(month, 0))

        services_fig = go.Figure()

        # Linha principal (mês atual)
        services_fig.add_trace(go.Scatter(
            x=month_names,
            y=service_counts,
            mode='lines+markers',
            line_shape='spline',  # suaviza a linha (forma de onda)
            line=dict(color=marker_color, width=3),
            marker=dict(size=6, color=marker_color),
            hovertemplate='<b>%{x}</b><br>Serviços: %{y}<extra></extra>',
            name='Serviços'
        ))

        # Linha comparativa (exemplo de meses anteriores)
        prev_year_counts = [max(0, y - 5) for y in service_counts]

        services_fig.update_layout(
            margin=dict(t=40, b=30, l=40, r=20),
            plot_bgcolor=plot_bg_color,
            paper_bgcolor=paper_bg_color,
            title={
                'text': f'Serviços por Mês ({ "Últimos 12 meses" if time_range == "12months" else "Últimos 6 meses" })', 
                'x': 0.5, 
                "xanchor": "center", 
                "font": {"color": font_color, "size": 14}
            },
            font=dict(color=font_color),
            xaxis=dict(
                title='Mês',
                title_font=dict(color=font_color),
                tickfont=dict(color=font_color),
                gridcolor=grid_color,
                linecolor=grid_color,
                zerolinecolor=grid_color
            ),
            yaxis=dict(
                title='Número de Serviços',
                title_font=dict(color=font_color),
                tickfont=dict(color=font_color),
                gridcolor=grid_color,
                linecolor=grid_color,
                zerolinecolor=grid_color
            )
        )
        
    except Exception as e:
        fallback_months = ['Jan/24', 'Fev/24', 'Mar/24', 'Abr/24', 'Mai/24', 'Jun/24']
        fallback_data = [15, 22, 18, 25, 30, 28]
        
        if time_range == '12months':
            fallback_months = ['Jul/23', 'Ago/23', 'Set/23', 'Out/23', 'Nov/23', 'Dez/23', 'Jan/24', 'Fev/24', 'Mar/24', 'Abr/24', 'Mai/24', 'Jun/24']
            fallback_data = [10, 15, 12, 18, 22, 20, 25, 28, 30, 25, 22, 20]
        
        services_fig = go.Figure(
            data=[go.Bar(x=fallback_months, y=fallback_data, marker=dict(color=marker_color))]
        )
        services_fig.update_layout(
            margin=dict(t=40, b=30, l=40, r=20),
            plot_bgcolor=plot_bg_color,
            paper_bgcolor=paper_bg_color,
            title={'text': f'Serviços por Mês ({ "Últimos 12 meses" if time_range == "12months" else "Últimos 6 meses" })', 'x': 0.5, "xanchor": "center", "font": {"color": font_color}},
            font=dict(color=font_color)
        )

    return graphOcurrence, GraphMapOcurrence, most_common_table, neighborhoods_table, services_fig


@callback(
    Output('value-agents', 'children'),
    Output('flux', 'children'),
    Input('interval', 'n_intervals'),
    State('theme-mode', 'data')
)
def att_flux(n, theme):
    try:
        logged_in_agents = fb.get_logged_in_agents()
        current_agents = len(logged_in_agents)
        
        all_agents = fb.get_all_agents()
        total_agents = len(all_agents)
        
        if total_agents > 0:
            percentage_logged = (current_agents / total_agents) * 100
            
            if current_agents == 0:
                status = "Nenhum ativo"
                icon_class = 'fas fa-times-circle'
                cor = '#ef4444'
                flux_text = '0%'
            elif percentage_logged >= 60:
                status = "Alta atividade"
                icon_class = 'fas fa-arrow-up'
                cor = '#10B981'
                flux_text = f'{percentage_logged:.0f}%'
            elif percentage_logged >= 30:
                status = "Atividade normal"
                icon_class = 'fas fa-check-circle'
                cor = '#3b82f6'
                flux_text = f'{percentage_logged:.0f}%'
            else:
                status = "Baixa atividade"
                icon_class = 'fas fa-arrow-down'
                cor = '#f59e0b'
                flux_text = f'{percentage_logged:.0f}%'
                
        else:
            status = "Sem dados"
            icon_class = 'fas fa-question-circle'
            cor = '#6b7280'
            flux_text = 'Nenhum agente cadastrado'
            
    except Exception as e:
        current_agents = 0
        status = "Erro de conexão"
        icon_class = 'fas fa-exclamation-triangle'
        cor = '#ef4444'
        flux_text = 'Verifique o Firebase'

    return (
        html.Span(f'{current_agents}', style={'color': 'var(--primary-text-color)'}),
        html.Div([
            html.I(className=icon_class, style={'color': cor, 'margin-right': '8px'}),
            html.Span(flux_text, style={'color': cor})
        ])
    )