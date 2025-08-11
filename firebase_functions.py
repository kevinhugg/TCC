import firebase_admin
from firebase_admin import credentials, firestore

#inicializa o app uma vez só
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

#BUSCAS

#busca viatura por numero
def get_vehicle_by_number(numero):
    docs = db.collection('veiculos').where('numero', '==', numero).stream()
    return next((doc.to_dict() for doc in docs), None)

#busca as partes que estao avariadas
def get_partes_avariadas(veiculo_id):
    try:
        inspecoes_ref = db.collection('veiculos').document(veiculo_id).collection('inspecoes')
        docs = inspecoes_ref.order_by('__name__', direction=firestore.Query.DESCENDING).limit(1).stream()

        avarias = []

        for doc in docs:
            dados = doc.to_dict()
            for parte, info in dados.items():
                if isinstance(info, dict) and (info.get("0") == 1 or info.get("descricao") or info.get("uriFoto")):
                    avarias.append({
                        "parte": parte.capitalize(),
                        "descricao": info.get("descricao", "Sem descrição"),
                        "imagem": info.get("uriFoto", "")
                    })

        return avarias

    except Exception as e:
        print(f"Erro ao buscar avarias detalhadas: {e}")
        return []

#busca agentes pela matricula
def get_agent_by_id(matricula):
    doc_ref = db.collection('agentes').document(matricula)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict() | {'id': doc.id}
    return None

#buscar ocorrências por viatura
def get_all_agents():
    docs = db.collection('agentes').stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

#agentes sem função
def get_unassigned_agents():
    docs = db.collection('agentes').where('funcao', '==', "").stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

#busca ocorrencias por agente pela subcoleção
def get_ocurrences_by_agent(agent_mat):
    ocorrencias_ref = db.collection('agentes').document(agent_mat).collection('ocorrencias')
    docs = ocorrencias_ref.stream()
    return next((doc.to_dict() | {'matricula': doc.id} for doc in docs))

#busca ocorrencias de todos os agentes na viatura informada
def get_ocurrences_by_vehicles(veiculo_numero):
    ocorrencias = []

    # Itera sobre todos os dias com ocorrências
    dias_docs = db.collection('ocorrencias').list_documents()

    for dia_doc in dias_docs:
        data_str = dia_doc.id  # Nome do doc = data (ex: "2025-08-06")

        lista_ref = dia_doc.collection('lista').stream()

        for doc in lista_ref:
            data = doc.to_dict()
            if data.get('viatura') == veiculo_numero:
                ocorrencias.append({
                    'id': doc.id,
                    'data': data_str,
                    'nome': data.get('nome'),
                    'agente': data.get('agente')
                })

    return ocorrencias

#pega agentes com o veiculo
def get_agents_by_vehicle(viatura_numero):
    docs = db.collection('agentes').where('viatura', '==', viatura_numero).stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]


#UPDATES

#att agente por id/matricula
def update_agent(agent_mat, updates: dict):
    db.collection('agentes').document(agent_mat).update(updates)

#remove atribuiçoes do agente
def clear_agent_assignment(agent_mat):
    update_agent(agent_mat, {
        'funcao': '',
        'viatura': '',
        'turno': '',
    })