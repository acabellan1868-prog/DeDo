"""Cliente HTTP para notificar gastos de compra a FiDo."""

import logging

import httpx

from app.config import FIDO_API_URL

logger = logging.getLogger("dedo.fido")


def notificar_gasto(importe: float, comercio: str, fecha: str) -> bool:
    """Envía un gasto de compra a FiDo.

    Devuelve True si FiDo lo aceptó, False en cualquier error.
    El fallo nunca se propaga — el ticket se guarda igualmente.
    """
    if not FIDO_API_URL:
        logger.warning("FIDO_API_URL no configurada — gasto no notificado")
        return False

    payload = {"importe": importe, "comercio": comercio, "fecha": fecha}
    try:
        respuesta = httpx.post(
            f"{FIDO_API_URL}/api/movimientos",
            json=payload,
            timeout=5,
        )
        respuesta.raise_for_status()
        logger.info("Gasto notificado a FiDo: %.2f€ en %s (%s)", importe, comercio, fecha)
        return True
    except httpx.TimeoutException:
        logger.error("FiDo no respondió en el tiempo límite — gasto no notificado")
    except httpx.HTTPStatusError as exc:
        logger.error("FiDo respondió con error %s — gasto no notificado", exc.response.status_code)
    except Exception as exc:
        logger.error("Error inesperado al notificar a FiDo: %s", exc)
    return False
