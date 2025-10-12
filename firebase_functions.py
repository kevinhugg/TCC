import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import base64
import uuid
from urllib.parse import quote
import requests
import os
from datetime import datetime

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'tcc-semurb-2ea61.firebasestorage.app'
    })

db = firestore.client()

def sign_in_user(email, password):
    api_key = os.environ.get("FIREBASE_WEB_API_KEY")
    if not api_key:
        return None, "Erro de configuração do servidor."

    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(rest_api_url, json=payload)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.HTTPError as err:
        error_json = err.response.json()
        error_message = error_json.get("error", {}).get("message", "Erro desconhecido.")
        
        if error_message == "INVALID_LOGIN_CREDENTIALS":
            return None, "Credenciais inválidas."
        return None, "Erro ao tentar fazer login."
    except Exception as e:
        return None, "Ocorreu um erro inesperado no servidor."

def create_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return user
    except Exception as e:
        error_str = str(e)
        if "EMAIL_EXISTS" in error_str:
            return "EMAIL_EXISTS"
        if "Password must be a string with at least 6 characters" in error_str:
            return "WEAK_PASSWORD"
        return None

def reset_password(email, new_password):
    try:
        user = auth.get_user_by_email(email)
        uid = user.uid
        auth.update_user(uid, password=new_password)
        return True, "Senha redefinida com sucesso."
    except auth.UserNotFoundError:
        return False, "Usuário não encontrado."
    except Exception as e:
        return False, f"Erro ao redefinir a senha: {e}"

def get_all_vehicles():
    docs = db.collection('veiculos').stream()
    vehicles = [doc.to_dict() for doc in docs]
    return vehicles

def get_vehicle_by_number(numero):
    docs = db.collection('veiculos').where('numero', '==', numero).stream()
    return next((doc.to_dict() for doc in docs), None)

def get_all_damage_reports():
    reports = []
    veiculos_ref = db.collection('veiculos').stream()

    for veiculo in veiculos_ref:
        veiculo_data = veiculo.to_dict()
        veiculo_id = veiculo.id

        inspecoes_ref = (
            db.collection('veiculos')
            .document(veiculo_id)
            .collection('inspecoes')
            .stream()
        )

        for inspecao in inspecoes_ref:
            inspecao_data = inspecao.to_dict()
            data_inspecao = inspecao.id

            for parte, danos in inspecao_data.items():
                if isinstance(danos, list):
                    for dano_info in danos:
                        if isinstance(dano_info, dict):
                            descricao = dano_info.get("descricao", "").strip()
                            uri_foto = dano_info.get("uriFoto", "").strip()

                            if descricao or uri_foto:
                                reports.append({
                                    "viatura": veiculo_data.get('numero', 'Sem número'),
                                    "parte": parte,
                                    "descricao": descricao if descricao else "Sem descrição",
                                    "status": "Aberta",
                                    "data": data_inspecao
                                })
    return reports

def get_damage_reports_by_vehicle(numero):
    reports = []
    veiculos_ref = db.collection('veiculos').where('numero', '==', numero).limit(1).stream()
    veiculo_doc = next(veiculos_ref, None)

    if veiculo_doc:
        veiculo_id = veiculo_doc.id
        veiculo_data = veiculo_doc.to_dict()

        inspecoes_ref = (
            db.collection('veiculos')
            .document(veiculo_id)
            .collection('inspecoes')
            .stream()
        )

        for inspecao in inspecoes_ref:
            inspecao_data = inspecao.to_dict()
            data_inspecao = inspecao.id

            for parte, danos in inspecao_data.items():
                if isinstance(danos, list):
                    for i, dano_info in enumerate(danos):
                        if isinstance(dano_info, dict):
                            descricao = dano_info.get("descricao", "").strip()
                            uri_foto = dano_info.get("uriFoto", "").strip()

                            if descricao or uri_foto:
                                raw_id = f"{veiculo_id}:{data_inspecao}:{parte}:{i}"
                                damage_id = base64.urlsafe_b64encode(raw_id.encode()).decode()

                                reports.append({
                                    "id": damage_id,
                                    "viatura": veiculo_data.get('numero', 'Sem número'),
                                    "parte": parte,
                                    "descricao": descricao if descricao else "Sem descrição",
                                    "status": "Aberta",
                                    "data": data_inspecao,
                                    "uriFoto": uri_foto
                                })
    return reports

def get_damage_by_id(damage_id):
    try:
        decoded_id = base64.urlsafe_b64decode(damage_id.encode()).decode()
        veiculo_id, data_inspecao, parte, index_str = decoded_id.split(':')
        index = int(index_str)

        inspecao_doc = db.collection('veiculos').document(veiculo_id).collection('inspecoes').document(data_inspecao).get()

        if not inspecao_doc.exists:
            return None

        inspecao_data = inspecao_doc.to_dict()
        danos_lista = inspecao_data.get(parte)

        if isinstance(danos_lista, list) and 0 <= index < len(danos_lista):
            dano_info = danos_lista[index]
            veiculo_doc = db.collection('veiculos').document(veiculo_id).get()
            veiculo_data = veiculo_doc.to_dict() if veiculo_doc.exists else {}

            return {
                "id": damage_id,
                "viatura": veiculo_data.get('numero', 'N/A'),
                "parte": parte,
                "descricao": dano_info.get("descricao", "Sem descrição"),
                "data": data_inspecao,
                "uriFoto": dano_info.get("uriFoto", "")
            }
        return None

    except Exception as e:
        return None

def delete_damage_by_id(damage_id):
    try:
        decoded_id = base64.urlsafe_b64decode(damage_id.encode()).decode()
        veiculo_id, data_inspecao, parte, index_str = decoded_id.split(':')
        index = int(index_str)

        inspection_ref = db.collection('veiculos').document(veiculo_id).collection('inspecoes').document(data_inspecao)
        inspection_doc = inspection_ref.get()

        if not inspection_doc.exists:
            return False

        inspection_data = inspection_doc.to_dict()
        damages_list = inspection_data.get(parte)

        if not isinstance(damages_list, list) or not (0 <= index < len(damages_list)):
            return False

        damages_list.pop(index)

        if not damages_list:
            inspection_ref.update({parte: firestore.DELETE_FIELD})
            updated_doc = inspection_ref.get().to_dict()
            if not updated_doc:
                inspection_ref.delete()
        else:
            inspection_ref.update({parte: damages_list})

        return True

    except Exception as e:
        return False

def get_agent_by_doc_id(agent_id):
    doc_ref = db.collection('agentes').document(agent_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict() | {'id': doc.id}
    return None

def get_all_agents():
    docs = db.collection('agentes').stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def get_all_adms():
    docs = db.collection('adm').stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def get_adm_by_uid(uid):
    try:
        docs = db.collection('adm').where('uid', '==', uid).stream()
        for doc in docs:
            return doc.to_dict() | {'id': doc.id}
        return None
    except Exception as e:
        return None

def get_admin_by_uid(uid):
    try:
        docs = db.collection('adm').where('uid', '==', uid).stream()
        for doc in docs:
            return doc.to_dict() | {'id': doc.id}
        return None
    except Exception as e:
        return None

def get_unassigned_agents():
    docs = db.collection('agentes').where('funcao', '==', "").stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def get_history_by_agent(agent_id):
    history = []
    if not agent_id:
        return history

    ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
    date_docs = ocorrencias_ref.stream()

    for date_doc in date_docs:
        data_str = date_doc.id
        lista_ref = date_doc.reference.collection('lista').stream()

        for item_doc in lista_ref:
            data = item_doc.to_dict()
            item_class = data.get('class', 'ocorrencia')
            item_type = 'Serviço' if item_class == 'serviço' else 'Ocorrência'

            history.append({
                'id': item_doc.id,
                'data': data_str,
                'descricao': data.get('nomenclatura', 'N/A'),
                'tipo': item_type,
                'class': item_class,
                'path': 'services' if item_class == 'serviço' else 'ocurrences',
                'viatura': data.get('viatura', 'N/A')
            })
    return history

def get_occurrences_and_services_by_vehicle(veiculo_numero):
    history = []
    agents = get_all_agents()

    for agent in agents:
        agent_id = agent.get('id')
        if not agent_id:
            continue

        ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
        date_docs = ocorrencias_ref.stream()

        for date_doc in date_docs:
            data_str = date_doc.id
            lista_ref = date_doc.reference.collection('lista').stream()

            for item_doc in lista_ref:
                data = item_doc.to_dict()
                if data.get('viatura') == veiculo_numero:
                    item_class = data.get('class', 'ocorrencia')
                    item_type = 'Serviço' if item_class == 'serviço' else 'Ocorrência'

                    history.append({
                        'id': item_doc.id,
                        'data': data_str,
                        'nomenclatura': data.get('nomenclatura', 'N/A'),
                        'tipo': item_type,
                        'class': item_class,
                        'path': 'services' if item_class == 'serviço' else 'ocurrences',
                        'viatura': data.get('viatura', 'N/A')
                    })
    return history

def get_all_occurrences_and_services():
    history = []
    agents = get_all_agents()

    for agent in agents:
        agent_id = agent.get('id')
        if not agent_id:
            continue

        agent_name = agent.get('nome', 'N/A')

        ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
        date_docs = ocorrencias_ref.stream()

        for date_doc in date_docs:
            data_str = date_doc.id
            lista_ref = date_doc.reference.collection('lista').stream()

            for item_doc in lista_ref:
                data = item_doc.to_dict()
                item_class = data.get('class', 'ocorrencia')
                item_type = 'Serviço' if item_class == 'serviço' else 'Ocorrência'

                history.append({
                    'id': item_doc.id,
                    'data': data_str,
                    'nomenclatura': data.get('nomenclatura', 'N/A'),
                    'tipo': item_type,
                    'class': item_class,
                    'path': 'services' if item_class == 'serviço' else 'ocurrences',
                    'viatura': data.get('viatura', 'N/A'),
                    'responsavel': agent_name,
                    'responsavel_id': agent_id
                })
    return history

def get_agents_by_vehicle(viatura_numero):
    docs = db.collection('agentes').where('viatura', '==', viatura_numero).stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def upload_image_to_storage(contents, filename, folder="viaturas"):
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')
        unique_filename = f"{folder}/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        download_token = uuid.uuid4()
        metadata = {"firebaseStorageDownloadTokens": str(download_token)}
        blob.metadata = metadata

        blob.upload_from_string(decoded, content_type=content_type)

        encoded_path = quote(blob.name, safe='')
        download_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}?alt=media&token={download_token}"

        return download_url, unique_filename
    except Exception as e:
        return None, None

def add_adm(adm_data):
    try:
        doc_ref = db.collection('adm').document()
        doc_ref.set(adm_data)
        return doc_ref.id
    except Exception as e:
        return None

def add_occurrence_or_service(agent_id, date, data):
    try:
        agent_ref = db.collection('agentes').document(agent_id)
        day_ref = agent_ref.collection('ocorrencias').document(date)
        day_ref.collection('lista').add(data)
        return True
    except Exception as e:
        return False

def add_vehicle(vehicle_data):
    try:
        doc_ref = db.collection('veiculos').document()
        doc_ref.set(vehicle_data)
        return doc_ref.id
    except Exception as e:
        return None

def delete_agent(agent_id):
    try:
        db.collection('agentes').document(agent_id).delete()
        return True
    except Exception as e:
        return False

def delete_vehicle(numero):
    try:
        docs = db.collection('veiculos').where('numero', '==', numero).limit(1).stream()
        doc_to_delete = next(docs, None)

        if doc_to_delete:
            doc_to_delete.reference.delete()
            return True
        else:
            return False
    except Exception as e:
        return False

def update_agent_by_doc_id(agent_id, updates: dict):
    db.collection('agentes').document(agent_id).update(updates)

def update_vehicle(numero, updates: dict):
    try:
        docs = db.collection('veiculos').where('numero', '==', numero).limit(1).stream()
        doc_to_update = next(docs, None)

        if doc_to_update:
            doc_to_update.reference.update(updates)
            return True
        else:
            return False
    except Exception as e:
        return False

def update_adm_by_doc_id(doc_id, update_data):
    try:
        adm_ref = db.collection('adm').document(doc_id)
        adm_ref.update(update_data)
        return True
    except Exception as e:
        return False

def replace_vehicle_image(numero, contents, filename):
    try:
        viatura = get_vehicle_by_number(numero)
        if not viatura:
            return None

        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')

        old_path = viatura.get("imagemPath")
        if old_path:
            try:
                bucket.blob(old_path).delete()
            except Exception:
                pass

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        unique_filename = f"viaturas/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        download_token = uuid.uuid4()
        metadata = {"firebaseStorageDownloadTokens": str(download_token)}
        blob.metadata = metadata

        blob.upload_from_string(decoded, content_type=content_type)

        encoded_path = quote(blob.name, safe='')
        download_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}"
            f"?alt=media&token={download_token}"
        )

        update_vehicle(numero, {
            "imagem": download_url,
            "imagemPath": unique_filename
        })

        return download_url

    except Exception as e:
        return None

def replace_agent_image(agent_id, contents, filename):
    try:
        agente = get_agent_by_doc_id(agent_id)
        if not agente:
            return None

        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')

        old_path = agente.get("foto_path")
        if old_path:
            try:
                bucket.blob(old_path).delete()
            except Exception:
                pass

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        unique_filename = f"agentes/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        download_token = uuid.uuid4()
        metadata = {"firebaseStorageDownloadTokens": str(download_token)}
        blob.metadata = metadata

        blob.upload_from_string(decoded, content_type=content_type)

        encoded_path = quote(blob.name, safe='')
        download_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}"
            f"?alt=media&token={download_token}"
        )

        update_agent_by_doc_id(agent_id, {
            "foto_agnt": download_url,
            "foto_path": unique_filename
        })

        return download_url

    except Exception as e:
        return None

def replace_adm_image(adm_id, contents, filename):
    try:
        adm_ref = db.collection('adm').document(adm_id)
        adm_doc = adm_ref.get()
        
        if not adm_doc.exists:
            return None

        adm_data = adm_doc.to_dict()
        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')

        old_path = adm_data.get("foto_path")
        if old_path:
            try:
                bucket.blob(old_path).delete()
            except Exception:
                pass

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        unique_filename = f"adms/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        download_token = uuid.uuid4()
        metadata = {"firebaseStorageDownloadTokens": str(download_token)}
        blob.metadata = metadata

        blob.upload_from_string(decoded, content_type=content_type)

        encoded_path = quote(blob.name, safe='')
        download_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}"
            f"?alt=media&token={download_token}"
        )

        update_adm_by_doc_id(adm_id, {
            "foto_agnt": download_url,
            "foto_path": unique_filename
        })

        return download_url

    except Exception as e:
        return None

def clear_agent_assignment(agent_id):
    update_agent_by_doc_id(agent_id, {
        'funcao': '',
        'viatura': '',
        'turno': '',
    })

def get_occurrence_or_service_by_id(doc_id):
    agents = get_all_agents()
    for agent in agents:
        agent_id = agent.get('id')
        if not agent_id:
            continue

        ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
        date_docs = ocorrencias_ref.stream()

        for date_doc in date_docs:
            lista_ref = date_doc.reference.collection('lista')
            doc = lista_ref.document(doc_id).get()
            if doc.exists:
                return doc.to_dict() | {'id': doc.id, 'data': date_doc.id}
    return None

def get_all_occurrence_types():
    try:
        docs = db.collection('tipos_ocorrencia').stream()
        occurrence_types = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            occurrence_types.append(data)
        return occurrence_types
    except Exception as e:
        return []

def add_occurrence_type(occurrence_data):
    try:
        existing_types = db.collection('tipos_ocorrencia')\
                          .where('tipo', '==', occurrence_data['tipo'])\
                          .stream()
        
        if any(existing_types):
            return False, "Este tipo de ocorrência já existe"
        
        doc_ref = db.collection('tipos_ocorrencia').document()
        occurrence_data['id'] = doc_ref.id
        doc_ref.set(occurrence_data)
        
        return True, "Tipo de ocorrência adicionado com sucesso"
        
    except Exception as e:
        return False, f"Erro ao adicionar: {str(e)}"

def update_occurrence_type(doc_id, update_data):
    try:
        doc_ref = db.collection('tipos_ocorrencia').document(doc_id)
        doc_ref.update(update_data)
        return True
    except Exception as e:
        return False

def delete_occurrence(agent_id, date, occurrence_id):
    try:
        from urllib.parse import unquote
        decoded_occurrence_id = unquote(occurrence_id)
        
        occurrence_ref = (
            db.collection('agentes')
            .document(agent_id)
            .collection('ocorrencias')
            .document(date)
            .collection('lista')
            .document(decoded_occurrence_id)
        )
        
        if occurrence_ref.get().exists:
            occurrence_ref.delete()
            return True
        else:
            return False
        
    except Exception as e:
        return False

def add_occurrence(occurrence_data):
    try:
        agent_id = occurrence_data.get('agent_id')
        if not agent_id:
            return False, "ID do agente é obrigatório"
        
        agent_ref = db.collection('agentes').document(agent_id)
        if not agent_ref.get().exists:
            return False, "Agente não encontrado"
        
        occurrence_date = occurrence_data.get('data')
        occurrence_time = datetime.now().strftime('%H:%Mh')
        
        date_ref = agent_ref.collection('ocorrencias').document(occurrence_date)
        lista_ref = date_ref.collection('lista')
        
        existing_occurrences = list(lista_ref.stream())
        occurrence_number = len(existing_occurrences) + 1
        
        occurrence_id = f"{occurrence_time} - {occurrence_number}"
        
        agent_data = agent_ref.get().to_dict()
        agent_name = agent_data.get('nome', 'N/A')
        agent_vehicle = agent_data.get('viatura', 'N/A')
        
        occurrence_info = {
            'id': occurrence_id,
            'class': 'ocorrencia',
            'nomenclatura': occurrence_data.get('tipo_ocorrencia', 'Ocorrência'),
            'tipo_ocorrencia': occurrence_data.get('tipo_ocorrencia', 'Geral'),
            'tipo': occurrence_data.get('tipo_ocorrencia', 'Geral'),
            'viatura': occurrence_data.get('viatura', agent_vehicle),
            'descricao': occurrence_data.get('descricao', ''),
            'horario_envio': occurrence_time,
            'data_envio': datetime.now().strftime('%d/%m/%Y'),
            'timestamp_ocorrencia': firestore.SERVER_TIMESTAMP,
            'responsavel': agent_name,
            'responsavel_id': agent_id,
            'numero_sequencial': occurrence_number
        }
        
        occurrence_ref = lista_ref.document(occurrence_id)
        occurrence_ref.set(occurrence_info)
        
        return True, "Ocorrência adicionada com sucesso"
        
    except Exception as e:
        return False, f"Erro ao adicionar ocorrência: {str(e)}"

def get_all_occurrences():
    try:
        all_occurrences = []
        agents = get_all_agents()
        
        for agent in agents:
            agent_id = agent.get('id')
            agent_name = agent.get('nome', 'N/A')
            agent_vehicle = agent.get('viatura', 'N/A')
            
            if not agent_id:
                continue
            
            ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
            date_docs = ocorrencias_ref.stream()
            
            for date_doc in date_docs:
                data_str = date_doc.id
                
                try:
                    lista_ref = date_doc.reference.collection('lista').stream()
                    
                    for occurrence_doc in lista_ref:
                        occurrence_data = occurrence_doc.to_dict()
                        occurrence_id = occurrence_doc.id
                        
                        if not occurrence_id:
                            continue
                            
                        is_occurrence = (
                            occurrence_data.get('class') == 'ocorrencia' or 
                            'tipo_ocorrencia' in occurrence_data or
                            'tipo' in occurrence_data
                        )
                        
                        if is_occurrence:
                            occurrence = {
                                'id': occurrence_id,
                                'data': data_str,
                                'horario': occurrence_data.get('horario_envio', 'N/A'),
                                'nomenclatura': occurrence_data.get('nomenclatura', 
                                                                   occurrence_data.get('tipo_ocorrencia', 'Ocorrência')),
                                'viatura': occurrence_data.get('viatura', agent_vehicle),
                                'tipo_ocorrencia': occurrence_data.get('tipo_ocorrencia', 'Geral'),
                                'descricao': occurrence_data.get('descricao', ''),
                                'responsavel': occurrence_data.get('responsavel', agent_name),
                                'responsavel_id': occurrence_data.get('responsavel_id', agent_id),
                                'class': 'ocorrencia'
                            }
                            
                            optional_fields = ['fotoUrl', 'endereco', 'contato', 'numcontato', 'numero_sequencial']
                            for field in optional_fields:
                                if field in occurrence_data:
                                    occurrence[field] = occurrence_data[field]
                            
                            all_occurrences.append(occurrence)
                            
                except Exception:
                    continue
        
        return all_occurrences
        
    except Exception as e:
        return []

def get_occurrence_by_id(occurrence_id):
    try:
        from urllib.parse import unquote
        decoded_occurrence_id = unquote(occurrence_id)
        
        agents = get_all_agents()
        
        for agent in agents:
            agent_id = agent.get('id')
            agent_name = agent.get('nome', 'N/A')
            
            if not agent_id:
                continue
            
            ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
            date_docs = list(ocorrencias_ref.stream())
            
            for date_doc in date_docs:
                data_str = date_doc.id
                
                try:
                    lista_ref = date_doc.reference.collection('lista')
                    occurrence_doc = lista_ref.document(decoded_occurrence_id).get()
                    
                    if occurrence_doc.exists:
                        occurrence_data = occurrence_doc.to_dict()
                        
                        return {
                            'id': decoded_occurrence_id,
                            'data': data_str,
                            'horario': occurrence_data.get('horario_envio', 'N/A'),
                            'nomenclatura': occurrence_data.get('nomenclatura', 'Ocorrência'),
                            'tipo_ocorrencia': occurrence_data.get('tipo_ocorrencia', 'Geral'),
                            'descricao': occurrence_data.get('descricao', ''),
                            'nome': occurrence_data.get('nome', ''),
                            'endereco': occurrence_data.get('endereco', ''),
                            'contato': occurrence_data.get('contato', ''),
                            'viatura': occurrence_data.get('viatura', agent.get('viatura', 'N/A')),
                            'responsavel': occurrence_data.get('responsavel', agent_name),
                            'responsavel_id': occurrence_data.get('responsavel_id', agent_id),
                            'fotoUrl': occurrence_data.get('fotoUrl', ''),
                            'class': 'ocorrencia'
                        }
                        
                except Exception:
                    continue
        
        return None
        
    except Exception as e:
        return None

def add_agent(agent_data):
    try:
        doc_ref = db.collection('agentes').document()
        agent_id = doc_ref.id
        agent_data['id'] = agent_id
        agent_data['data_criacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        doc_ref.set(agent_data)
        
        matricula = agent_data.get('matricula', '').strip()
        nome = agent_data.get('nome', '')
        
        if matricula and nome:
            auth_success, auth_message = create_agent_auth_user(matricula, nome)
        
        return True
        
    except Exception as e:
        return False

def create_agent_auth_user(matricula, nome):
    try:
        email = f"{matricula}@gmail.com"
        password = "123456"
        
        user = auth.create_user(
            email=email,
            password=password,
            display_name=nome
        )
        
        return True, f"Usuário criado com email: {email} e senha: {password}"
        
    except auth.EmailAlreadyExistsError:
        return False, "Este email já está em uso"
    except ValueError as e:
        return False, f"Erro de validação: {e}"
    except Exception as e:
        return False, f"Erro ao criar usuário: {e}"

def update_agent(agent_id, update_data):
    try:
        db.collection('agentes').document(agent_id).update(update_data)
        return True
    except Exception as e:
        return False

def get_agent_by_id(agent_id):
    try:
        doc_ref = db.collection('agentes').document(agent_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    except Exception as e:
        return None

def assign_agent_to_vehicle(agent_id, vehicle_number, funcao, turno):
    try:
        update_data = {
            'viatura': vehicle_number,
            'funcao': funcao,
            'turno': turno
        }
        db.collection('agentes').document(agent_id).update(update_data)
        return True
    except Exception as e:
        return False

def remove_agent_from_vehicle(agent_id):
    try:
        update_data = {
            'viatura': '',
            'funcao': '',
            'turno': ''
        }
        db.collection('agentes').document(agent_id).update(update_data)
        return True
    except Exception as e:
        return False

def get_equipe_options():
    return ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"]

def get_funcao_options():
    return ["encarregado", "motorista", "agente", "supervisor", "operador"]

def get_patente_options():
    return ["soldado", "cabo", "sargento", "tenente", "capitao", "major", "coronel"]

def get_all_services():
    try:
        all_services = []
        
        viario_ref = db.collection('viario')
        date_docs = viario_ref.stream()
        
        for date_doc in date_docs:
            data_str = date_doc.id
            
            try:
                lista_ref = date_doc.reference.collection('lista').stream()
                
                for service_doc in lista_ref:
                    service_data = service_doc.to_dict()
                    service_id = service_doc.id
                    
                    if not service_id:
                        continue
                    
                    service = {
                        'id': service_id,
                        'data': data_str,
                        'horario': service_data.get('horario_envio', service_id.split(' - ')[0] if ' - ' in service_id else 'N/A'),
                        'nomenclatura': service_data.get('topico', 'Serviço de Viário'),
                        'tipo': service_data.get('tipo', 'Serviço Viário'),
                        'descricao': service_data.get('descricao', ''),
                        'endereco': service_data.get('endereco', ''),
                        'qtd_items': service_data.get('qtd_items', 1),
                        'numero_sequencial': service_data.get('numero_sequencial', 1),
                        'data_envio': service_data.get('data_envio', ''),
                        'class': 'serviço'
                    }
                    
                    agents = get_all_agents()
                    agent_responsavel = None
                    
                    for agent in agents:
                        agent_viario_ref = db.collection('agentes').document(agent['id']).collection('viario')
                        agent_date_doc = agent_viario_ref.document(data_str).get()
                        
                        if agent_date_doc.exists:
                            agent_responsavel = agent
                            break
                    
                    if agent_responsavel:
                        service['responsavel'] = agent_responsavel.get('nome', 'N/A')
                        service['responsavel_id'] = agent_responsavel.get('id', '')
                        service['viatura'] = agent_responsavel.get('viatura', 'N/A')
                    else:
                        service['responsavel'] = 'N/A'
                        service['responsavel_id'] = ''
                        service['viatura'] = 'N/A'
                    
                    all_services.append(service)
                    
            except Exception:
                continue
        
        return all_services
        
    except Exception as e:
        return []

def get_all_services_with_agents():
    try:
        all_services = []
        
        agents = get_all_agents()
        
        for agent in agents:
            agent_id = agent.get('id')
            agent_name = agent.get('nome', 'N/A')
            agent_vehicle = agent.get('viatura', 'N/A')
            
            if not agent_id:
                continue
            
            viario_ref = db.collection('agentes').document(agent_id).collection('viario')
            
            try:
                date_docs = list(viario_ref.stream())
                
                for date_doc in date_docs:
                    data_str = date_doc.id
                    
                    try:
                        lista_ref = date_doc.reference.collection('lista')
                        service_docs = list(lista_ref.stream())
                        
                        for service_doc in service_docs:
                            service_data = service_doc.to_dict()
                            service_id = service_doc.id
                            
                            service = {
                                'id': service_id,
                                'data': data_str,
                                'horario': service_data.get('horario_envio', service_id.split(' - ')[0] if ' - ' in service_id else 'N/A'),
                                'nomenclatura': service_data.get('topico', 'Serviço de Viário'),
                                'tipo': service_data.get('tipo', service_data.get('topico', 'Serviço Viário')),
                                'descricao': service_data.get('descricao', ''),
                                'endereco': service_data.get('endereco', ''),
                                'responsavel': agent_name,
                                'responsavel_id': agent_id,
                                'viatura': agent_vehicle,
                                'qtd_items': service_data.get('qtd_items', 1),
                                'numero_sequencial': service_data.get('numero_sequencial', 1),
                                'data_envio': service_data.get('data_envio', ''),
                                'class': 'serviço'
                            }
                            
                            optional_fields = ['fotoUrl', 'local', 'observacoes']
                            for field in optional_fields:
                                if field in service_data:
                                    service[field] = service_data[field]
                            
                            all_services.append(service)
                            
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        return all_services
        
    except Exception as e:
        return []

def get_service_by_id(service_id):
    try:
        from urllib.parse import unquote
        decoded_service_id = unquote(service_id)
        
        agents = get_all_agents()
        
        for agent in agents:
            agent_id = agent.get('id')
            agent_name = agent.get('nome', 'N/A')
            agent_vehicle = agent.get('viatura', 'N/A')
            
            if not agent_id:
                continue
            
            viario_ref = db.collection('agentes').document(agent_id).collection('viario')
            date_docs = list(viario_ref.stream())
            
            for date_doc in date_docs:
                data_str = date_doc.id
                
                try:
                    lista_ref = date_doc.reference.collection('lista')
                    service_doc = lista_ref.document(decoded_service_id).get()
                    
                    if service_doc.exists:
                        service_data = service_doc.to_dict()
                        
                        return {
                            'id': decoded_service_id,
                            'data': data_str,
                            'horario': service_data.get('horario_envio', decoded_service_id.split(' - ')[0] if ' - ' in decoded_service_id else 'N/A'),
                            'nomenclatura': service_data.get('topico', 'Serviço de Viário'),
                            'tipo': service_data.get('tipo', 'Serviço Viário'),
                            'descricao': service_data.get('descricao', ''),
                            'local': service_data.get('local', ''),
                            'endereco': service_data.get('endereco', ''),
                            'observacoes': service_data.get('observacoes', ''),
                            'viatura': agent_vehicle,
                            'responsavel': agent_name,
                            'responsavel_id': agent_id,
                            'fotoUrl': service_data.get('fotoUrl', ''),
                            'qtd_items': service_data.get('qtd_items', 1),
                            'numero_sequencial': service_data.get('numero_sequencial', 1),
                            'data_envio': service_data.get('data_envio', ''),
                            'class': 'serviço'
                        }
                        
                except Exception:
                    continue
        
        return None
        
    except Exception as e:
        return None

def add_service(service_data):
    try:
        agent_id = service_data.get('agent_id')
        if not agent_id:
            return False, "ID do agente é obrigatório"
        
        agent_ref = db.collection('agentes').document(agent_id)
        if not agent_ref.get().exists:
            return False, "Agente não encontrado"
        
        service_date = service_data.get('data')
        service_time = datetime.now().strftime('%H:%Mh')
        
        viario_ref = agent_ref.collection('viario').document(service_date)
        lista_ref = viario_ref.collection('lista')
        
        existing_services = list(lista_ref.stream())
        service_number = len(existing_services) + 1
        
        service_id = f"{service_time} - {service_number}"
        
        agent_data = agent_ref.get().to_dict()
        agent_name = agent_data.get('nome', 'N/A')
        agent_vehicle = agent_data.get('viatura', 'N/A')
        
        service_info = {
            'id': service_id,
            'class': 'serviço',
            'nomenclatura': service_data.get('tipo_servico', 'Serviço de Viário'),
            'tipo_servico': service_data.get('tipo_servico', 'Geral'),
            'viatura': service_data.get('viatura', agent_vehicle),
            'descricao': service_data.get('descricao', ''),
            'local': service_data.get('local', ''),
            'endereco': service_data.get('endereco', ''),
            'observacoes': service_data.get('observacoes', ''),
            'horario_envio': service_time,
            'data_envio': datetime.now().strftime('%d/%m/%Y'),
            'timestamp_servico': firestore.SERVER_TIMESTAMP,
            'responsavel': agent_name,
            'responsavel_id': agent_id,
            'numero_sequencial': service_number
        }
        
        service_ref = lista_ref.document(service_id)
        service_ref.set(service_info)
        
        return True, "Serviço adicionado com sucesso"
        
    except Exception as e:
        return False, f"Erro ao adicionar serviço: {str(e)}"

def get_all_service_types():
    try:
        docs = db.collection('tipos_servico').stream()
        service_types = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            service_types.append(data)
        return service_types
    except Exception as e:
        return []

def add_service_type(service_data):
    try:
        existing_types = db.collection('tipos_servico')\
                          .where('nome', '==', service_data['nome'])\
                          .stream()
        
        if any(existing_types):
            return False, "Este tipo de serviço já existe"
        
        doc_ref = db.collection('tipos_servico').document()
        service_data['id'] = doc_ref.id
        service_data['data_criacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        doc_ref.set(service_data)
        
        return True, "Tipo de serviço adicionado com sucesso"
        
    except Exception as e:
        return False, f"Erro ao adicionar: {str(e)}"

def update_service_type(doc_id, update_data):
    try:
        doc_ref = db.collection('tipos_servico').document(doc_id)
        doc_ref.update(update_data)
        return True
    except Exception as e:
        return False

def delete_service_type(doc_id):
    try:
        db.collection('tipos_servico').document(doc_id).delete()
        return True
    except Exception as e:
        return False

def delete_service(service_id):
    try:
        from urllib.parse import unquote
        decoded_service_id = unquote(service_id)
        
        agents = get_all_agents()
        
        for agent in agents:
            agent_id = agent.get('id')
            
            if not agent_id:
                continue
            
            viario_ref = db.collection('agentes').document(agent_id).collection('viario')
            date_docs = list(viario_ref.stream())
            
            for date_doc in date_docs:
                data_str = date_doc.id
                
                try:
                    lista_ref = date_doc.reference.collection('lista')
                    service_doc = lista_ref.document(decoded_service_id).get()
                    
                    if service_doc.exists:
                        lista_ref.document(decoded_service_id).delete()
                        
                        remaining_services = list(lista_ref.stream())
                        if not remaining_services:
                            date_doc.reference.delete()
                        
                        return True, "Serviço deletado com sucesso"
                        
                except Exception:
                    continue
        
        return False, "Serviço não encontrado"
        
    except Exception as e:
        return False, f"Erro ao deletar serviço: {str(e)}"

def get_logged_in_agents():
    try:
        all_agents = get_all_agents()
        logged_in_agents = []
        
        for agent in all_agents:
            if agent.get('viatura') and agent.get('viatura') != '':
                logged_in_agents.append(agent)
        
        return logged_in_agents
        
    except Exception as e:
        return []

def get_services_this_month():
    try:
        all_services = get_all_services()
        current_month = datetime.now().strftime('%Y-%m')
        
        services_this_month = [
            s for s in all_services 
            if s.get('data', '').startswith(current_month)
        ]
        
        return len(services_this_month)
        
    except Exception as e:
        return 0

def get_occurrences_this_month():
    try:
        all_occurrences = get_all_occurrences()
        current_month = datetime.now().strftime('%Y-%m')
        
        occurrences_this_month = [
            o for o in all_occurrences 
            if o.get('data', '').startswith(current_month)
        ]
        
        return len(occurrences_this_month)
        
    except Exception as e:
        return 0

def create_admin_user(email, password, nome, matricula):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=nome
        )
        
        admin_data = {
            "nome": nome,
            "email": email,
            "matricula": matricula,
            "uid": user.uid,
            "tipo": "admin",
            "data_criacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "permissoes": ["criar_agentes", "gerenciar_usuarios", "acesso_total"]
        }
        
        doc_ref = db.collection('adm').document()
        doc_ref.set(admin_data)
        
        return True
        
    except Exception as e:
        return False