from savebasket_data.normalization.quantity_parser import parse_quantity


def test_parse_quantity_extracts_basic_weight() -> None:
    assert parse_quantity("Jumbo Snack Worteltjes 300 g") == (300, "g")


def test_parse_quantity_extracts_decimal_liters() -> None:
    assert parse_quantity("Coca-Cola Zero 1,5L") == (1.5, "l")


def test_parse_quantity_extracts_multipack_volume() -> None:
    assert parse_quantity("Fristi 6 x 200 ml") == (1200, "ml")


def test_parse_quantity_extracts_piece_count() -> None:
    assert parse_quantity("Croissant 4 stuks") == (4, "pc")


def test_parse_quantity_returns_none_for_unsupported_text() -> None:
    assert parse_quantity("zonder inhoud") == (None, None)
