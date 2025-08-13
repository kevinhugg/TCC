import firebase_admin
from firebase_admin import credentials, firestore

# inicializa o app uma vez só
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)

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


# busca ocorrencias de todos os agentes na viatura informada
def get_occurrences_and_services_by_vehicle(veiculo_numero):
    history = []
    dias_docs = db.collection('ocorrencias').list_documents()

    for dia_doc in dias_docs:
        data_str = dia_doc.id
        lista_ref = dia_doc.collection('lista').stream()

        for doc in lista_ref:
            data = doc.to_dict()
            if data.get('viatura') == veiculo_numero:
                item_class = data.get('class', 'ocorrencia')
                item_type = 'Serviço' if item_class == 'serviço' else 'Ocorrência'

                history.append({
                    'id': doc.id,
                    'data': data_str,
                    'nomenclatura': data.get('nomenclatura', 'N/A'),
                    'tipo': item_type,
                    'class': item_class,
                    'path': 'services' if item_class == 'serviço' else 'ocurrences'
                })

    return history


# pega agentes com o veiculo
def get_agents_by_vehicle(viatura_numero):
    docs = db.collection('agentes').where('viatura', '==', viatura_numero).stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]


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