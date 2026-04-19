from savebasket_data.normalization.price_parser import parse_price


def test_parse_price_handles_decimal_comma_and_currency_noise() -> None:
    assert parse_price("€ 1,99") == 1.99


def test_parse_price_handles_thousands_separator_and_decimal_comma() -> None:
    assert parse_price("EUR 1.234,56") == 1234.56


def test_parse_price_returns_none_for_unusable_values() -> None:
    assert parse_price("gratis") is None
