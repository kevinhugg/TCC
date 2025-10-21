import dash
from dash import html, dcc, Input, Output, callback, State
import firebase_functions as fb
from flask import session
import urllib.parse

dash.register_page(__name__, path='/profile', name='Perfil', className='pg-at')

def get_profile_image_url(adm_data):
    foto_path = adm_data.get('foto_agnt', '')
    
    if not foto_path :
        return '/static/assets/img/personaa.png'
    
    if foto_path.startswith('http'):
        return foto_path
    
    if 'agentes/' in foto_path or 'adms/' in foto_path:
        if 'agentes/' in foto_path:
            filename = foto_path.replace('agentes/', '')
        else:
            filename = foto_path.replace('adms/', '')
            
        encoded_filename = urllib.parse.quote(filename, safe='')
        bucket_name = "tcc-semurb-2ea61.appspot.com"
        firebase_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/agentes%2F{encoded_filename}?alt=media"
        
        return firebase_url
    
    return '/static/assets/img/personaa.png'

def layout():
    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/profile.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        
        dcc.Store(id='user-store', data={'user_id': session.get('user_id', '')}),
        dcc.Store(id='current-adm-data'),
        dcc.Store(id='profile-trigger', data=0),
        dcc.Store(id='user-profile-image', data={'profile_image': '/static/assets/img/personaa.png'}),
        dcc.ConfirmDialog(id='update-confirm-profile', message=''),
        dcc.Interval(id='interval-component', interval=1000, n_intervals=0, max_intervals=1),
        
        html.Div(
            id='upload-modal',
            className='modal profile-modal',
            style={'display': 'none'},
            children=[
                html.Div(
                    className='modal-content',
                    children=[
                        html.Div(className='modal-header', children=[
                            html.H5('Alterar Foto de Perfil', className='profile-title'),
                            html.Button('×', id='close-modal', className='close-btn')
                        ]),
                        html.Div(className='modal-body', children=[
                            dcc.Upload(
                                id='upload-image',
                                children=html.Div([
                                    'Arraste ou Clique para Selecionar uma Imagem'
                                ], className='profile-text'),
                                style={
                                    'width': '100%',
                                    'height': '200px',
                                    'lineHeight': '200px',
                                    'borderWidth': '2px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px 0',
                                    'borderColor': 'var(--border-color)',
                                    'backgroundColor': 'var(--card-bg-color)',
                                    'color': 'var(--primary-text-color)'
                                },
                                multiple=False,
                                accept='image/*'
                            ),
                            html.Div(id='upload-preview', style={'display': 'none'}, children=[
                                html.Img(id='preview-image', style={'maxWidth': '200px', 'maxHeight': '200px'}),
                                html.Button('Remover', id='remove-preview', n_clicks=0, className='btn btn-secondary')
                            ])
                        ]),
                        html.Div(className='modal-footer', children=[
                            html.Button('Cancelar', id='cancel-upload', n_clicks=0, className='btn btn-secondary'),
                            html.Button('Salvar', id='save-image', n_clicks=0, className='btn btn-primary')
                        ])
                    ]
                )
            ]
        ),

        html.Div([
            html.Div([
                html.Div([
                    html.Div(
                        id='profile-image-wrapper',
                        className='profile-image-wrapper',
                        n_clicks=0,
                        children=[
                            html.Img(
                                id='profile-image',
                                className='profile-pic-large',
                                src='/static/assets/img/personaa.png'
                            )
                        ]
                    ),
                    
                    html.Div(id='profile-info', className='profile-info-container'),
                    
                ], className='profile-container')
            ], className='page-content')
        ])
    ])

@callback(
    [Output('profile-info', 'children'),
     Output('profile-image', 'src'),
     Output('current-adm-data', 'data'),
     Output('user-profile-image', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('profile-trigger', 'data')],
    State('user-store', 'data')
)
def load_profile_data(n, trigger, user_data):
    try:
        user_id = user_data.get('user_id')
        
        if not user_id:
            return [
                html.H3("Usuário não identificado", className='profile-title'),
                html.P("Faça login novamente", className='profile-text'),
            ], '/static/assets/img/personaa.png', {}, {'profile_image': '/static/assets/img/personaa.png'}
        
        adms = fb.get_all_adms()
        
        current_adm = None
        for adm in adms:
            adm_uid = adm.get('uid')
            if adm_uid == user_id:
                current_adm = adm
                break
        
        if not current_adm:
            return [
                html.H3("Administrador não encontrado", className='profile-title'),
                html.P("Contate o suporte do sistema", className='profile-text'),
            ], '/static/assets/img/personaa.png', {}, {'profile_image': '/static/assets/img/personaa.png'}

        image_url = get_profile_image_url(current_adm)
        
        profile_elements = [
            html.H3(current_adm.get('nome', 'Nome não informado'), className='profile-title'),
            
            html.Div([
                html.Span("Email: ", className='profile-label'),
                html.Span(current_adm.get('email', 'Não informado'), className='profile-value')
            ], className='profile-field'),
            
            html.Div([
                html.Span("Matrícula: ", className='profile-label'),
                html.Span(current_adm.get('matricula', 'Não informada'), className='profile-value')
            ], className='profile-field'),
        ]
        
        if current_adm.get('cargo_at'):
            profile_elements.append(
                html.Div([
                    html.Span("Cargo: ", className='profile-label'),
                    html.Span(current_adm['cargo_at'], className='profile-value')
                ], className='profile-field')
            )
        
        if current_adm.get('func_mes'):
            profile_elements.append(
                html.Div([
                    html.Span("Função: ", className='profile-label'),
                    html.Span(current_adm['func_mes'], className='profile-value')
                ], className='profile-field')
            )
        
        adm_data_for_store = current_adm.copy()
        profile_image_data = {'profile_image': image_url}
        
        return profile_elements, image_url, adm_data_for_store, profile_image_data
        
    except Exception:
        return [
            html.H3("Erro ao carregar", className='profile-title'),
            html.P("Tente recarregar a página", className='profile-text'),
        ], '/static/assets/img/personaa.png', {}, {'profile_image': '/static/assets/img/personaa.png'}

@callback(
    Output('upload-modal', 'style'),
    [Input('profile-image-wrapper', 'n_clicks'),
     Input('close-modal', 'n_clicks'),
     Input('cancel-upload', 'n_clicks'),
     Input('save-image', 'n_clicks')]
)
def toggle_modal(open_clicks, close_clicks, cancel_clicks, save_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'profile-image-wrapper' and open_clicks:
        return {'display': 'block'}
    elif button_id in ['close-modal', 'cancel-upload', 'save-image']:
        return {'display': 'none'}
    
    return dash.no_update

@callback(
    [Output('upload-preview', 'style'),
     Output('preview-image', 'src')],
    [Input('upload-image', 'contents'),
     Input('remove-preview', 'n_clicks')]
)
def update_preview(contents, remove_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'remove-preview' and remove_clicks:
        return {'display': 'none'}, ''
    elif button_id == 'upload-image' and contents:
        return {'display': 'block', 'textAlign': 'center'}, contents
    
    return dash.no_update, dash.no_update

@callback(
    [Output('update-confirm-profile', 'displayed'),
     Output('update-confirm-profile', 'message'),
     Output('profile-trigger', 'data')],
    Input('save-image', 'n_clicks'),
    [State('upload-image', 'contents'),
     State('upload-image', 'filename'),
     State('current-adm-data', 'data')]
)
def save_adm_image(save_clicks, contents, filename, adm_data):
    if not save_clicks:
        return False, "", dash.no_update
    
    if not contents:
        return True, "Por favor, selecione uma imagem", dash.no_update
    
    adm_id = adm_data.get('id')
    if not adm_id:
        return True, "ID do administrador não encontrado", dash.no_update
    
    try:
        foto_url, foto_path = fb.upload_image_to_storage(contents, filename, folder="adms")
        
        if foto_url:
            update_data = {
                'foto_agnt': foto_url,
                'foto_path': foto_path
            }
            
            success = fb.update_adm_by_doc_id(adm_id, update_data)
            
            if success:
                return True, "Foto de perfil atualizada com sucesso!", 1
            else:
                return True, "Erro ao atualizar perfil no banco de dados", dash.no_update
        else:
            return True, "Erro ao fazer upload da imagem", dash.no_update
            
    except Exception as e:
        return True, f"Erro: {str(e)}", dash.no_update

@callback(
    [Output('profile-image', 'src', allow_duplicate=True),
     Output('user-profile-image', 'data', allow_duplicate=True)],
    Input('profile-trigger', 'data'),
    State('current-adm-data', 'data'),
    prevent_initial_call=True
)
def refresh_after_update(trigger, adm_data):
    if trigger:
        try:
            adm_id = adm_data.get('id')
            if adm_id:
                adms = fb.get_all_adms()
                current_adm = next((adm for adm in adms if adm.get('id') == adm_id), None)
                if current_adm:
                    image_url = get_profile_image_url(current_adm)
                    return image_url, {'profile_image': image_url}
        except Exception:
            pass
    
    return dash.no_update, dash.no_update