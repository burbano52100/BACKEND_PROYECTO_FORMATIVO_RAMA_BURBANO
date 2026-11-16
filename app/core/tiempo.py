"""Fecha y hora oficiales del sistema (Colombia, UTC-5, sin horario de verano)."""

# calendar sirve para saber cuántos días tiene un mes
import calendar
# Tipos para trabajar con fechas, horas, duraciones y zonas horarias
from datetime import date, datetime, time, timedelta, timezone

# Zona horaria de Colombia: 5 horas menos que UTC (Colombia no cambia la hora en el año)
ZONA_COLOMBIA = timezone(timedelta(hours=-5), "America/Bogota")


# Devuelve la fecha y hora actuales en Colombia
def ahora() -> datetime:
    # datetime.now con zona horaria evita depender de la hora configurada en el servidor
    return datetime.now(ZONA_COLOMBIA)


# Devuelve solo la fecha de hoy en Colombia (sin la hora)
def hoy() -> date:
    # .date() quita la parte de la hora
    return ahora().date()


# Indica si un momento está dentro de un horario
def en_horario(momento: datetime, inicio: time, fin: time) -> bool:
    """True si la hora del momento está entre inicio y fin (ambos incluidos)."""
    # Compara solo la hora (.time()); "<=" incluye los extremos (7:00 y 21:00 cuentan)
    return inicio <= momento.time() <= fin


# Devuelve el último día del mes de una fecha (por ejemplo 2026-11-16 -> 2026-11-30)
def ultimo_dia_del_mes(fecha: date) -> date:
    # monthrange devuelve (día de la semana del día 1, cantidad de días del mes); se usa el segundo
    return fecha.replace(day=calendar.monthrange(fecha.year, fecha.month)[1])
