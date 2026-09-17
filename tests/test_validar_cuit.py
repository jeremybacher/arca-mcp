"""Tests de `server.validar_cuit`: valida que el CUIT tenga 11 dígitos
numéricos, permitiendo guiones y espacios en los bordes."""

import pytest

from server import validar_cuit


@pytest.mark.parametrize(
    "cuit",
    [
        "20304050607",  # 11 dígitos sin separadores
        "20-30405060-7",  # con guiones, formato habitual de CUIT
        "  20304050607  ",  # con espacios en los extremos
        "27111222339",
    ],
)
def test_cuit_valido(cuit):
    assert validar_cuit(cuit) is True


@pytest.mark.parametrize(
    "cuit",
    [
        "",
        "123",  # muy corto
        "203040506070",  # muy largo (12 dígitos)
        "2030405060a",  # contiene una letra
        "20-3040-5060",  # separadores raros pero igual sobran/faltan dígitos
        "abcdefghijk",  # solo letras
        "20 30405060 7a",  # con letra intercalada
    ],
)
def test_cuit_invalido(cuit):
    assert validar_cuit(cuit) is False
