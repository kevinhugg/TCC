viaturas = [
    {'id': 1, 'placa': 'ABC-1234', 'numero': 'V001', 'veiculo': 'Carro', 'avariada': True, 'loc_av': 'Para-choque',  'imagem': '/static/assets/img/viatura1.png'},
    {'id': 2, 'placa': 'DEF-5678', 'numero': 'V002', 'veiculo': 'Moto', 'avariada': False, 'loc_av': False, 'imagem': '/static/assets/img/viatura1.png'},
    {'id': 3, 'placa': 'GHI-9012', 'numero': 'V003', 'veiculo': 'Carro', 'avariada': True, 'loc_av': 'Capô', 'imagem': '/static/assets/img/viatura1.png'},
    {'id': 4, 'placa': 'JKL-3456', 'numero': 'V004', 'veiculo': 'Caminhão', 'avariada': False, 'loc_av': False, 'imagem': '/static/assets/img/viatura1.png'},
]

agents = [
    {'id': '1a', 'nome': 'João Augusto', 'cargo_at': 'Fiscal de Meio Ambiente', 'func_mes': 'Auxiliar', 'viatura_mes': 'V001', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '2a', 'nome': 'Kleber Rochas', 'cargo_at': 'Arquiteto Urbanista', 'func_mes': 'Motorista', 'viatura_mes': 'V001', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '3a', 'nome': 'Armando Silva', 'cargo_at': 'Engenheiro Ambiental', 'func_mes': 'Encarregado', 'viatura_mes': 'V001', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
    {'id': '4a', 'nome': 'Joares Santos', 'cargo_at': 'Engenheiro Civil', 'func_mes': 'encarregado', 'viatura_mes': 'V004', 'foto_agnt': '/static/assets/img/agent_photo.jpeg'},
]

damVehicles = [
    {'viatura': 'V001', 'descricao': 'Pane no motor', 'status': 'Aberta', 'data': '07/07/2025'},
    {'viatura': 'V003', 'descricao': 'Pneu furado', 'status': 'Fechada', 'data': '06/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
    {'viatura': 'V002', 'descricao': 'Falha elétrica', 'status': 'Aberta', 'data': '05/07/2025'},
]

#agrupamento das datas dos danos em veiculos
data_damVeh = [item['data'] for item in damVehicles]

time_response = {
    '2023': [30, 28, 40, 23, 50, 69, 20, 40, 64, 34, 23],
    '2024': [36, 56, 45, 23, 23, 32, 21, 31, 64, 34, 12],
    '2025': [43, 45, 67, 78, 23, 34, 53, 63, 37, 23, 23]
}

#infos Ocorrências mais comuns
Most_common_Ocu = [
    {'tipo': 'Sinístro de Trânsito', 'quantidade': 120, 'viatura': 'V001', 'data': '2025-07-25', 'id': 'a1'},
    {'tipo': 'Semáforo Apagado', 'quantidade': 85, 'viatura': 'V001', 'data': '2025-05-25', 'id': 'a2'},
    {'tipo': 'Veículo Danificado na Via', 'quantidade': 60, 'viatura': 'V001', 'data': '2025-02-01', 'id': 'a3'},
    {'tipo': 'Obstrução na Pista', 'quantidade': 45, 'viatura': 'V001', 'data': '2025-07-30', 'id': 'a4'},
    {'tipo': 'Vazamento de Água na pista', 'quantidade': 20, 'viatura': 'V001', 'data': '2025-02-10', 'id': 'a5'},
]

#Dados do Mapa
Ocur_Neighborhoods = [
    {'bairro': 'Centro', 'latitude': -23.5505, 'longitude': -46.6333, 'quantidade': 120},
    {'bairro': 'Jardins', 'latitude': -23.5614, 'longitude': -46.6550, 'quantidade': 95},
    {'bairro': 'Moema', 'latitude': -23.6011, 'longitude': -46.6647, 'quantidade': 85},
    {'bairro': 'Tatuapé', 'latitude': -23.5401, 'longitude': -46.5764, 'quantidade': 70},
    {'bairro': 'Pinheiros', 'latitude': -23.5611, 'longitude': -46.6792, 'quantidade': 60},
]

#Dados Ocorrências
Ocur_Vehicles = [
    {
        'viatura': 'V001',
        'id': 'aa',
        'nomenclatura': 'Atendimento ao cidadão',
        'descricao': 'Cidadão solicitou ajuda com o veículo',
        'endereco': 'Rua José Martinez N°11',
        'n_cidadao': 'Kleber Machado',
        'contato': '(11) 98154-8217',
        'data': '2025-07-05',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'ab',
        'nomenclatura': 'Sinistro de Trânsito',
        'descricao': 'Realizamos a remoção de um veículo na via',
        'endereco': 'Rua Yuri Alberto Garro',
        'n_cidadao': 'Keber Machado',
        'contato': '(11) 98154-8217',
        'data': '2025-07-05',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'ab',
        'nomenclatura': 'Sinistro de Grande Vulto',
        'descricao': 'Realizamos a remoção de um veículo na via',
        'endereco': 'Rua Yuri Alberto Garro',
        'n_cidadao': 'Keber Machado',
        'contato': '(11) 98154-8217',
        'data': '2025-07-05',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'b',
        'nomenclatura': ' ambiental',
        'descricao': 'Atendimento à denúncia',
        'data': '2025-06-22',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'c',
        'nomenclatura': 'Fiscalização ',
        'descricao': 'Fiscalização ambiental',
        'data': '2025-07-05',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'd',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Atendimento à denúncia',
        'data': '2025-06-22',
        'class': 'serviço'
    },
{
        'viatura': 'V001',
        'id': 'e',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Fiscalização ambiental',
        'data': '2025-07-05',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'f',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Atendimento à denúncia',
        'data': '2025-06-22',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'g',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Fiscalização ambiental',
        'data': '2025-07-05',
        'class': 'serviço'
    },
    {
        'viatura': 'V001',
        'id': 'h',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Atendimento à denúncia',
        'data': '2025-06-22',
        'class': 'serviço'
    },
    {
        'viatura': 'V002',
        'id': 'i',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'serviço'
    },
    {
        'viatura': 'V002',
        'id': 'j',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'serviço'
    },
    {
        'viatura': 'V002',
        'id': 'k',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'serviço'
    },
    {
        'viatura': 'V002',
        'id': 'l',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'serviço'
    },
    {
        'viatura': 'V002',
        'id': 'm',
        'nomenclatura': 'Fiscalização ambiental',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'serviço'
    },
    {
        'viatura': 'V003',
        'nomenclatura': 'Fiscalização ambiental',
        'id': 'n',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'ocorrencia'
    },
    {
        'viatura': 'V003',
        'nomenclatura': 'Fiscalização ambiental',
        'id': 'o',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'ocorrencia'
    },
    {
        'viatura': 'V003',
        'nomenclatura': 'Fiscalização ambiental',
        'id': 'p',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'ocorrencia'
    },
    {
        'viatura': 'V003',
        'nomenclatura': 'Fiscalização ambiental',
        'id': 'q',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'ocorrencia'
    },
    {
        'viatura': 'V003',
        'nomenclatura': 'Fiscalização ambiental',
        'id': 'r',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'ocorrencia'
    },
    {
        'viatura': 'V003',
        'nomenclatura': 'Fiscalização ambiental',
        'id': 's',
        'descricao': 'Ronda noturna',
        'data': '2025-07-01',
        'class': 'ocorrencia'
    },
]
