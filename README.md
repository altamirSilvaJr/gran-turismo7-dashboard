# gran-turismo7-dashboard
Projeto para estudo e hobby consumindo telemetria do Gran Turismo 7 via UDP, com foco em visualização em tempo real, análise de voltas e comparação de traçados.

## Versionamento
| Versão | Data       | Modificações |
|--------|------------|--------------|
| 0.1.2  | 2026-02-24 | Janela de traçado com comparação por volta, estilos por throttle/brake, hover com dados por volta, limite de 10 voltas com descarte da pior, e painel de combustível dinâmico (consumo/voltas restantes). |

## Funcionalidades atuais
- Captura de telemetria do GT7 via UDP.
- Parsing de pacotes com campos de carro, corrida e física.
- Dashboard principal (velocidade, RPM, combustível, voltas e inputs).
- Janela de traçado com:
  - comparação entre voltas,
  - cor por volta,
  - estilos por estado de pedal (aceleração/freio/coast),
  - hover com tabela de aceleração/freio por volta no ponto mais próximo.
- Gestão de memória de voltas:
  - máximo de 10 voltas armazenadas,
  - ao exceder, remove a volta com pior tempo.
- Métricas de combustível:
  - consumo por volta,
  - estimativa de voltas restantes com base no consumo médio.

## Estrutura do projeto
```text
gran-turismo7/
|-- main.py
|-- README.md
|-- requirements.txt
|
|-- app/
|   |-- config.py
|   |-- telemetry.py
|   |-- services/
|   |   |-- __init__.py
|   |   `-- track_service.py
|   `-- ui/
|       |-- dashboard_window.py
|       |-- fuel_panel.py
|       |-- lap_info_panel.py
|       |-- rpm_gauge.py
|       |-- speed_hauge.py
|       |-- telemetry_graph.py
|       |-- track_window.py
|       `-- track_canvas.py
|
|-- domain/
|   |-- game_state.py
|   |-- track_state.py
|   `-- lap_telemetry.py
|
`-- infrastructure/
    |-- udp_client.py
    |-- packet_parser.py
    `-- crypto.py
```

## Mapa de offsets do pacote UDP
| Offset (hex) | Tipo de dado | Campo / significado |
|--------------|--------------|---------------------|
| 0x00 | não explorado | não explorado |
| 0x01 | não explorado | não explorado |
| 0x02 | não explorado | não explorado |
| 0x03 | não explorado | não explorado |
| 0x04 | float | position_x |
| 0x08 | float | position_y |
| 0x0C | float | position_z |
| 0x10 | float | velocity_x |
| 0x14 | float | velocity_y |
| 0x18 | float | velocity_z |
| 0x1C | float | rotation_pitch |
| 0x20 | float | rotation_yaw |
| 0x24 | float | rotation_roll |
| 0x2C | float | angular_velocity_x |
| 0x30 | float | angular_velocity_y |
| 0x34 | float | angular_velocity_z |
| 0x3C | float | rpm |
| 0x40 | int | seed IV |
| 0x41 | não explorado | não explorado |
| 0x42 | não explorado | não explorado |
| 0x43 | não explorado | não explorado |
| 0x44 | float | fuel |
| 0x48 | float | fuel_capacity |
| 0x4C | float | speed_mps |
| 0x50 | não explorado | boost |
| 0x54 | não explorado | oil pressure |
| 0x58 | não explorado | water temperature |
| 0x5C | não explorado | oil temperature |
| 0x60 | float | tyre_temp_fl |
| 0x64 | float | tyre_temp_fr |
| 0x68 | float | tyre_temp_rl |
| 0x6C | float | tyre_temp_rr |
| 0x70 | não explorado | packet_id |
| 0x74 | int16 | current_lap |
| 0x76 | uint16 | total_laps |
| 0x78 | int32 | best_lap (ms, convertido) |
| 0x7C | int32 | last_lap (ms, convertido) |
| 0x80 | uint32 | race_time (ms, convertido) |
| 0x84 | uint16 | current_position |
| 0x86 | uint16 | total_cars |
| 0x88 | uint16 | rpm_warn |
| 0x8A | uint16 | rpm_rev_limiter |
| 0x8C | não explorado | estimated_top_speed |
| 0x8E | uint8 | is_paused / is_in_race |
| 0x8F | não explorado | não explorado |
| 0x90 | uint8 | current_gear / suggested_gear |
| 0x91 | uint8 | throttle |
| 0x92 | uint8 | brake |
| 0x93 | não explorado | não explorado |
| ... | ... | ... |
| 0xB4 | float | tyre_diameter_fl |
| 0xB8 | float | tyre_diameter_fr |
| 0xBC | float | tyre_diameter_rl |
| 0xC0 | float | tyre_diameter_rr |
| 0xC4 | não explorado | não explorado |
| ... | ... | ... |
| 0xFF | não explorado | não explorado |

## Como executar
1. Crie/ative um ambiente virtual Python.
2. Instale as dependências:
   - `pip install -r requirements.txt`
3. Configure IP/portas em `app/config.py`.
4. Execute:
   - `python main.py`

## Observações
- O parser usa offsets conhecidos do pacote UDP do GT7 e alguns campos ainda podem evoluir.
- O cálculo de consumo por volta depende da transição entre voltas (fecha quando inicia a próxima volta).
