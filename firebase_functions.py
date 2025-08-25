import firebase_admin
from firebase_admin import credentials, firestore, storage
import base64
import uuid
from urllib.parse import quote

# inicializa o app uma vez só
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'tcc-semurb-2ea61.firebasestorage.app'
    })

db = firestore.client()


# BUSCAS

# Busca todos as viaturas
def get_all_vehicles():
    docs = db.collection('veiculos').stream()
    vehicles = [doc.to_dict() for doc in docs]
    return vehicles


# busca viatura por numero
def get_vehicle_by_number(numero):
    docs = db.collection('veiculos').where('numero', '==', numero).stream()
    return next((doc.to_dict() for doc in docs), None)


# busca as partes que estao avariadas
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
                                # Generate a unique ID
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
    """Gets a single damage report by its unique ID."""
    try:
        # Decode the ID
        decoded_id = base64.urlsafe_b64decode(damage_id.encode()).decode()
        veiculo_id, data_inspecao, parte, index_str = decoded_id.split(':')
        index = int(index_str)

        # Fetch the inspection document
        inspecao_doc = db.collection('veiculos').document(veiculo_id).collection('inspecoes').document(
            data_inspecao).get()

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
        print(f"Error fetching damage by ID {damage_id}: {e}")
        return None


def delete_damage_by_id(damage_id):
    """Deletes a single damage report by its unique ID."""
    try:
        decoded_id = base64.urlsafe_b64decode(damage_id.encode()).decode()
        veiculo_id, data_inspecao, parte, index_str = decoded_id.split(':')
        index = int(index_str)

        inspection_ref = db.collection('veiculos').document(veiculo_id).collection('inspecoes').document(data_inspecao)
        inspection_doc = inspection_ref.get()

        if not inspection_doc.exists:
            print(f"Inspection document not found for damage ID {damage_id}")
            return False

        inspection_data = inspection_doc.to_dict()
        damages_list = inspection_data.get(parte)

        if not isinstance(damages_list, list) or not (0 <= index < len(damages_list)):
            print(f"Damage not found at index {index} for part {parte}")
            return False

        # Remove the damage from the list
        damages_list.pop(index)

        # If the list is now empty, remove the part field from the document
        if not damages_list:
            inspection_ref.update({parte: firestore.DELETE_FIELD})
            # After removing the field, check if the document is now empty
            updated_doc = inspection_ref.get().to_dict()
            if not updated_doc:
                inspection_ref.delete()
                print(f"Deleted empty inspection document {data_inspecao}")
        else:
            # Otherwise, update the document with the modified list
            inspection_ref.update({parte: damages_list})

        print(f"Successfully deleted damage {damage_id}")
        return True

    except Exception as e:
        print(f"Error deleting damage by ID {damage_id}: {e}")
        return False


# busca agentes pelo id do documento
def get_agent_by_doc_id(agent_id):
    doc_ref = db.collection('agentes').document(agent_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict() | {'id': doc.id}
    return None


# buscar ocorrências por viatura
def get_all_agents():
    docs = db.collection('agentes').stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]


# agentes sem função
def get_unassigned_agents():
    docs = db.collection('agentes').where('funcao', '==', "").stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]


def get_history_by_agent(agent_id):
    """Gets all occurrences and services for a specific agent."""
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
                'descricao': data.get('nomenclatura', 'N/A'), # Assuming 'nomenclatura' is the description
                'tipo': item_type,
                'class': item_class,
                'path': 'services' if item_class == 'serviço' else 'ocurrences',
                'viatura': data.get('viatura', 'N/A')
            })
    return history


def get_occurrences_and_services_by_vehicle(veiculo_numero):
    """Gets all occurrences and services for a specific vehicle by iterating through agents."""
    history = []
    agents = get_all_agents()  # Fetch all agents

    for agent in agents:
        agent_id = agent.get('id')
        if not agent_id:
            continue

        # Reference to the 'ocorrencias' subcollection for the agent
        ocorrencias_ref = db.collection('agentes').document(agent_id).collection('ocorrencias')
        date_docs = ocorrencias_ref.stream()

        for date_doc in date_docs:
            data_str = date_doc.id
            lista_ref = date_doc.reference.collection('lista').stream()

            for item_doc in lista_ref:
                data = item_doc.to_dict()
                # Check if the item belongs to the requested vehicle
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
    """Gets all occurrences and services from all agents."""
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


# pega agentes com o veiculo
def get_agents_by_vehicle(viatura_numero):
    docs = db.collection('agentes').where('viatura', '==', viatura_numero).stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]


def upload_image_to_storage(contents, filename):
    """Uploads an image to Firebase Storage and returns its download URL."""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Força o nome do bucket diretamente para evitar problemas de descoberta
        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')
        unique_filename = f"viaturas/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        # Create a new token and set it in the metadata
        download_token = uuid.uuid4()
        metadata = {"firebaseStorageDownloadTokens": str(download_token)}
        blob.metadata = metadata

        # Upload the file
        blob.upload_from_string(decoded, content_type=content_type)

        # Manually construct the download URL
        encoded_path = quote(blob.name, safe='')
        download_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}?alt=media&token={download_token}"

        return download_url, unique_filename
    except Exception as e:
        print(f"An error occurred while uploading image: {e}")
        return None, None


# ADD / DELETE

def add_agent(agent_data):
    """Adds a new agent to the 'agentes' collection. Firestore will generate the ID."""
    try:
        doc_ref = db.collection('agentes').document()
        doc_ref.set(agent_data)
        return doc_ref.id
    except Exception as e:
        print(f"An error occurred while adding agent: {e}")
        return None


def add_occurrence_or_service(agent_id, date, data):
    """Adds a new occurrence or service to a specific agent's subcollection."""
    try:
        agent_ref = db.collection('agentes').document(agent_id)
        day_ref = agent_ref.collection('ocorrencias').document(date)
        day_ref.collection('lista').add(data)
        return True
    except Exception as e:
        print(f"An error occurred while adding occurrence/service for agent {agent_id}: {e}")
        return False


def add_vehicle(vehicle_data):
    """Adds a new vehicle to the 'veiculos' collection."""
    try:
        doc_ref = db.collection('veiculos').document()
        doc_ref.set(vehicle_data)
        return doc_ref.id
    except Exception as e:
        print(f"An error occurred while adding vehicle: {e}")
        return None


def delete_agent(agent_id):
    """Deletes an agent from the 'agentes' collection by their ID."""
    try:
        db.collection('agentes').document(agent_id).delete()
        return True
    except Exception as e:
        print(f"An error occurred while deleting agent {agent_id}: {e}")
        return False


def delete_vehicle(numero):
    """Deletes a vehicle from the 'veiculos' collection by its number."""
    try:
        # Find the document by its 'numero' field
        docs = db.collection('veiculos').where('numero', '==', numero).limit(1).stream()
        doc_to_delete = next(docs, None)

        if doc_to_delete:
            doc_to_delete.reference.delete()
            print(f"Vehicle with numero {numero} deleted successfully.")
            return True
        else:
            print(f"No vehicle found with numero {numero}.")
            return False
    except Exception as e:
        print(f"An error occurred while deleting vehicle {numero}: {e}")
        return False


# UPDATES

# att agente por id do documento
def update_agent_by_doc_id(agent_id, updates: dict):
    db.collection('agentes').document(agent_id).update(updates)


def update_vehicle(numero, updates: dict):
    """Atualiza um veículo na coleção 'veiculos' pelo seu número."""
    try:
        # Encontra o documento pelo campo 'numero'
        docs = db.collection('veiculos').where('numero', '==', numero).limit(1).stream()
        doc_to_update = next(docs, None)

        if doc_to_update:
            doc_to_update.reference.update(updates)
            print(f"Viatura com número {numero} atualizada com sucesso.")
            return True
        else:
            print(f"Nenhuma viatura encontrada com o número {numero}.")
            return False
    except Exception as e:
        print(f"Ocorreu um erro ao atualizar a viatura {numero}: {e}")
        return False


def replace_vehicle_image(numero, contents, filename):
    """Substitui a imagem de uma viatura: apaga a antiga e sobe a nova."""
    try:
        # 1. Busca a viatura
        viatura = get_vehicle_by_number(numero)
        if not viatura:
            print(f"Nenhuma viatura encontrada com numero {numero}")
            return None

        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')

        # 2. Apaga a imagem antiga (se existir)
        old_path = viatura.get("imagemPath")
        if old_path:
            try:
                bucket.blob(old_path).delete()
                print(f"Imagem antiga {old_path} apagada.")
            except Exception as e:
                print(f"Erro ao apagar imagem antiga: {e}")

        # 3. Sobe a nova
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

        # 4. Atualiza o Firestore
        update_vehicle(numero, {
            "imagem": download_url,
            "imagemPath": unique_filename
        })

        return download_url

    except Exception as e:
        print(f"Erro ao substituir imagem: {e}")
        return None


def replace_agent_image(agent_id, contents, filename):
    """Substitui a foto de um agente: apaga a antiga e sobe a nova."""
    try:
        # 1. Busca o agente
        agente = get_agent_by_doc_id(agent_id)
        if not agente:
            print(f"Nenhum agente encontrado com o ID {agent_id}")
            return None

        bucket = storage.bucket('tcc-semurb-2ea61.firebasestorage.app')

        # 2. Apaga a foto antiga do Storage (se existir um caminho salvo)
        old_path = agente.get("foto_path")
        if old_path:
            try:
                bucket.blob(old_path).delete()
                print(f"Foto antiga {old_path} apagada.")
            except Exception as e:
                # Se o arquivo não existir no storage, não há problema.
                print(f"Info: Não foi possível apagar a foto antiga (pode já ter sido removida): {e}")

        # 3. Faz upload da nova foto
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        unique_filename = f"agentes/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        download_token = uuid.uuid4()
        metadata = {"firebaseStorageDownloadTokens": str(download_token)}
        blob.metadata = metadata

        blob.upload_from_string(decoded, content_type=content_type)

        # Constrói a URL de download manualmente
        encoded_path = quote(blob.name, safe='')
        download_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}"
            f"?alt=media&token={download_token}"
        )

        # 4. Atualiza o documento do agente no Firestore com a nova URL e caminho
        update_agent_by_doc_id(agent_id, {
            "foto_agnt": download_url,
            "foto_path": unique_filename
        })

        return download_url

    except Exception as e:
        print(f"Erro ao substituir a foto do agente: {e}")
        return None


# remove atribuiçoes do agente
def clear_agent_assignment(agent_id):
    update_agent_by_doc_id(agent_id, {
        'funcao': '',
        'viatura': '',
        'turno': '',
    })


def get_occurrence_or_service_by_id(doc_id):
    """Gets a single occurrence or service by its unique ID, searching across all agents."""
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