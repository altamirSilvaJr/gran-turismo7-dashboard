from dataclasses import dataclass
import struct
from typing import Optional

@dataclass
class PhysicsData:
    # =========================
    # World Position
    # =========================
    # Coordenadas absolutas do carro no espaço 3D do circuito.
    # Representam a posição no sistema de referência global da pista.
    # OBS: o ponto (0,0,0) parece ser o centro da pista olhando para a imagem do minimapa, mas talvez isso pode variar dependendo do circuito.
    position_x: float
    position_y: float
    position_z: float

    # =========================
    # Linear Velocity
    # =========================
    # Velocidade do carro em cada eixo do mundo.
    # Pode conter valores negativos dependendo da direção do movimento.
    velocity_x: float
    velocity_y: float
    velocity_z: float

    # =========================
    # Rotation
    # =========================
    # Orientação do carro no espaço 3D.
    # Representa os ângulos de inclinação em cada eixo.
    rotation_pitch: float  # Inclinação frente/trás (nariz sobe/desce)
    rotation_yaw: float    # Rotação horizontal (direção do carro)
    rotation_roll: float   # Inclinação lateral (inclinação em curva)

    # =========================
    # Angular Velocity (rad/s)
    # =========================
    # Velocidade de rotação em cada eixo.
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float

@dataclass
class TelemetryData:
    throttle: float
    brake: float
    speed_kmh: float
    steering: Optional[float] = None
    rpm: Optional[float] = None
    rpm_warn: Optional[float] = None
    rpm_rev_limiter: Optional[float] = None
    gear: Optional[int] = None
    suggested_gear: Optional[int] = None
    fuel: Optional[float] = None
    best_lap: Optional[str] = None
    last_lap: Optional[str] = None
    current_lap: Optional[int] = None
    total_laps: Optional[int] = None
    current_position: Optional[int] = None
    total_cars: Optional[int] = None

def ms_to_time(ms: int, include_hours: bool = False) -> str:
    """
    Converte milissegundos para:
    - 'M:SS:MMM' por padrão (minutos:segundos:milissegundos)
    - 'H:MM:SS:MMM' se include_hours=True (horas:minutos:segundos:milissegundos)

    Exemplos:
    - ms_to_time(88365) -> "1:28:365"
    - ms_to_time(3723045, include_hours=True) -> "1:02:03"
    """
    if ms < 0:
        ms = 0

    if include_hours:
        hours = ms // 3_600_000
        rem = ms % 3_600_000
        minutes = rem // 60_000
        seconds = (rem % 60_000) // 1000
        milliseconds = rem % 1000
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        minutes = ms // 60_000
        seconds = (ms % 60_000) // 1000
        milliseconds = ms % 1000
        return f"{minutes}:{seconds:02d}:{milliseconds:03d}"

def _has_bytes(packet: bytes, offset: int, size: int) -> bool:
    """
    Valida se o packet tem bytes suficientes a partir do offset para ler o campo de tamanho 'size'.
    Parametros:
        - packet: bytes do packet a ser verificado
        - offset: posição inicial do campo a ser lido
        - size: quantidade de bytes que o campo ocupa
    """
    return len(packet) >= offset + size

def parse_telemetry(packet: bytes) -> TelemetryData:
    """
    Extrai campos básicos + exemplos de campos adicionais.
    Ajuste os offsets marcados como exemplo conforme o mapeamento real do packet.
    """
    #############
    # Car Infos #
    #############
    speed_kmh = 0.0
    rpm = None
    current_gear = None
    fuel = None
    if _has_bytes(packet, 0x4C, 4):
        speed_mps = struct.unpack_from("<f", packet, 0x4C)[0]
        speed_kmh = speed_mps * 3.6

    if _has_bytes(packet, 0x91, 1):
        throttle = packet[0x91] / 255.0 # Divide por 255 para normalizar entre 0.0 e 1.0
        # print(f"Throttle: {throttle}")
    else:
        throttle = 0.0
    if _has_bytes(packet, 0x92, 1):
        brake = packet[0x92] / 255.0 # Divide por 255 para normalizar entre 0.0 e 1.0
        # print(f"Brake: {brake}")
    else:
        brake = 0.0

    #############
    # Gear Info #
    #############

    if _has_bytes(packet, 0x90, 1):
        current_gear = packet[0x90] & 0x0F  # exemplo: byte único para a marcha atual
        suggested_gear = (packet[0x90] >> 4) & 0x0F
        if suggested_gear > 9:
            suggested_gear = "-"
        # print(f"Current Gear: {current_gear}, Suggested Gear: {suggested_gear}")

    #############
    # RPM Infos #
    #############
    if _has_bytes(packet, 0x3C, 4):
        rpm = struct.unpack_from("<f", packet, 0x3C)[0]
        # print(f"RPM: {rpm}")

    if _has_bytes(packet, 0x88, 2):
        rpm_warn = struct.unpack_from("<H", packet, 0x88)[0]
        # print(f"RPM Warning: {rpm_warn}")

    if _has_bytes(packet, 0x8A, 2):
        rpm_rev_limiter = struct.unpack_from("<H", packet, 0x8A)[0]
        # print(f"RPM Rev Limiter: {rpm_rev_limiter}")

    #############
    # Fuel Info #
    #############

    if _has_bytes(packet, 0x44, 4):
        fuel = struct.unpack_from("<f", packet, 0x44)[0]
        # print(f"Fuel: {fuel:.2f} %")

    if _has_bytes(packet, 0x48, 4):
        fuel_capacity = struct.unpack_from("<f", packet, 0x48)[0]
        # print(f"Fuel Capacity: {fuel_capacity:.2f} %")

    ##############
    # Laps Infos #
    ##############
    if _has_bytes(packet, 0x78, 4):
        best_lap = ms_to_time(struct.unpack_from("<i", packet, 0x78)[0])
        # print(f"Best Lap: {best_lap}")

    if _has_bytes(packet, 0x7C, 4):
        last_lap = ms_to_time(struct.unpack_from("<i", packet, 0x7C)[0])
        # print(f"Last Lap: {last_lap}")

    if _has_bytes(packet, 0x74, 2):
        current_lap = struct.unpack_from("<h", packet, 0x74)[0] # Not the current lap time. It's the current lap number.
        # print(f"Current Lap: {current_lap}")

    if _has_bytes(packet, 0x76, 2):
        total_laps = struct.unpack_from("<H", packet, 0x76)[0]
        # print(f"Total Laps: {total_laps}")

    ############
    # Race infos #
    ############
    if _has_bytes(packet, 0x80, 4):
        race_time = ms_to_time(struct.unpack_from("<I", packet, 0x80)[0], include_hours=True) # time of the day
        # print(f"Race Time: {race_time}")

    if _has_bytes(packet, 0x84, 2):
        current_position = struct.unpack_from("<H", packet, 0x84)[0] # current position
        # print(f"Current Position: {current_position}")

    if _has_bytes(packet, 0x86, 2):
        total_cars = struct.unpack_from("<H", packet, 0x86)[0] # total cars in the race
        # print(f"Total Cars: {total_cars}")

    if _has_bytes(packet, 0x8E, 1):
        is_paused = (packet[0x8E] & 0b00000010) != 0
        # print(f"Paused: {is_paused}")
        is_in_race = (packet[0x8E] & 0b00000001) != 0
        # print(f"In Race: {is_in_race}")

    if _has_bytes(packet, 0x04, 48):

        position = struct.unpack_from('<fff', packet, 0x04)
        velocity = struct.unpack_from('<fff', packet, 0x10)
        rotation = struct.unpack_from('<fff', packet, 0x1C)
        angular_velocity = struct.unpack_from('<fff', packet, 0x2C)

        physics_data = PhysicsData(
            position_x=position[0],
            position_y=position[1],
            position_z=position[2],

            velocity_x=velocity[0],
            velocity_y=velocity[1],
            velocity_z=velocity[2],

            rotation_pitch=rotation[0],
            rotation_yaw=rotation[1],
            rotation_roll=rotation[2],

            angular_velocity_x=angular_velocity[0],
            angular_velocity_y=angular_velocity[1],
            angular_velocity_z=angular_velocity[2],
        )


    ###############
    # Tyre infos #
    ###############
    # Diameter
    if _has_bytes(packet, 0xB4, 16):
        tyre_diameter_fl = struct.unpack_from("<f", packet, 0xB4)[0]
        tyre_diameter_fr = struct.unpack_from("<f", packet, 0xB8)[0]
        tyre_diameter_rl = struct.unpack_from("<f", packet, 0xBC)[0]
        tyre_diameter_rr = struct.unpack_from("<f", packet, 0xC0)[0]

    # Temperature
    if _has_bytes(packet, 0x60, 16):
        tyre_temp_fl = struct.unpack_from("<f", packet, 0x60)[0]
        tyre_temp_fr = struct.unpack_from("<f", packet, 0x64)[0]
        tyre_temp_rl = struct.unpack_from("<f", packet, 0x68)[0]
        tyre_temp_rr = struct.unpack_from("<f", packet, 0x6C)[0]
        # print(f"Tyre Temps: FL={tyre_temp_fl:.1f}°C FR={tyre_temp_fr:.1f}°C RL={tyre_temp_rl:.1f}°C RR={tyre_temp_rr:.1f}°C")


    return TelemetryData(
        throttle=throttle,
        brake=brake,
        speed_kmh=speed_kmh,
        rpm=rpm,
        rpm_warn=rpm_warn,
        rpm_rev_limiter=rpm_rev_limiter,
        gear=current_gear,
        suggested_gear=suggested_gear,
        fuel=fuel,
        best_lap=best_lap,
        last_lap=last_lap,
        current_lap=current_lap,
        total_laps=total_laps,
        current_position=current_position,
        total_cars=total_cars,
    )