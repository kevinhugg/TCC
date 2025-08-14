import firebase_admin
from firebase_admin import credentials, firestore, storage
import base64
import uuid

# inicializa o app uma vez só
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'tcc-semurb-2ea61.appspot.com'
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


def get_damages_dates():
    dates = []
    veiculos_ref = db.collection('veiculos').stream()

    for veiculo in veiculos_ref:
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
                                dates.append(data_inspecao)
                                break

    return dates


# busca agentes pela matricula
def get_agent_by_id(matricula):
    doc_ref = db.collection('agentes').document(matricula)
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


# busca ocorrencias por agente pela subcoleção
def get_ocurrences_by_agent(agent_mat):
    ocorrencias_ref = db.collection('agentes').document(agent_mat).collection('ocorrencias')
    docs = ocorrencias_ref.stream()
    return next((doc.to_dict() | {'matricula': doc.id} for doc in docs))


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
                    'viatura': data.get('viatura', 'N/A')
                })

    return history


# pega agentes com o veiculo
def get_agents_by_vehicle(viatura_numero):
    docs = db.collection('agentes').where('viatura', '==', viatura_numero).stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]


def upload_image_to_storage(contents, filename):
    """Uploads an image to Firebase Storage and returns its public URL."""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        bucket = storage.bucket()
        # Generate a unique filename
        unique_filename = f"viaturas/{uuid.uuid4()}-{filename}"
        blob = bucket.blob(unique_filename)

        blob.upload_from_string(decoded, content_type=content_type)
        blob.make_public()

        return blob.public_url
    except Exception as e:
        print(f"An error occurred while uploading image: {e}")
        return None


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


def add_service(agent_id, service_date, service_data):
    """Adds a new service for a specific agent."""
    return add_occurrence_or_service(agent_id, service_date, service_data)


def add_occurrence(agent_id, occ_date, occ_data):
    """Adds a new occurrence for a specific agent."""
    return add_occurrence_or_service(agent_id, occ_date, occ_data)


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


# UPDATES

# att agente por id/matricula
def update_agent(agent_mat, updates: dict):
    db.collection('agentes').document(agent_mat).update(updates)


# remove atribuiçoes do agente
def clear_agent_assignment(agent_mat):
    update_agent(agent_mat, {
        'funcao': '',
        'viatura': '',
        'turno': '',
    })


def get_occurrence_or_service_by_id(doc_id):
    dias_docs = db.collection('ocorrencias').list_documents()
    for dia_doc in dias_docs:
        doc_ref = dia_doc.collection('lista').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict() | {'id': doc.id, 'data': dia_doc.id}
    return None


def delete_occurrence_or_service(doc_id):
    dias_docs = db.collection('ocorrencias').list_documents()
    for dia_doc in dias_docs:
        doc_ref = dia_doc.collection('lista').document(doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            # Se a subcoleção 'lista' ficar vazia, remove o documento do dia
            if not dia_doc.collection('lista').limit(1).get():
                dia_doc.delete()
            return True
    return False