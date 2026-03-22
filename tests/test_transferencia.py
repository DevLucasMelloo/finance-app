from datetime import date
from domain.transferencia import Transferencia
from domain.lancamento import NatureType


def test_transferencia_basica():
    transferencia = Transferencia(
        transfer_date=date.today(),
        amount=5000,
        origin=NatureType.INVESTMENT,
        destination=NatureType.CASH,
        description="Resgate de investimento"
    )

    assert transferencia.amount == 5000
    assert transferencia.origin == NatureType.INVESTMENT
    assert transferencia.destination == NatureType.CASH
