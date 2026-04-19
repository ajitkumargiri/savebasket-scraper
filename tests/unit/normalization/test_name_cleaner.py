from savebasket_data.normalization.name_cleaner import clean_product_name


def test_clean_product_name_normalizes_spacing_units_and_case() -> None:
    assert clean_product_name(" Campina Halfvolle-Melk 1L ") == "campina halfvolle melk 1 l"


def test_clean_product_name_normalizes_decimal_quantities() -> None:
    assert clean_product_name("Coca-Cola Zero 1,5L") == "coca cola zero 1.5 l"


def test_clean_product_name_returns_empty_string_for_missing_value() -> None:
    assert clean_product_name(None) == ""
