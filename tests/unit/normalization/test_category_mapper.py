from savebasket_data.normalization.category_mapper import (
    map_source_category,
    map_source_category_group,
)


def test_map_source_category_slugifies_leaf_category() -> None:
    assert map_source_category('Jumbo', 'Verse zuivel') == 'verse-zuivel'


def test_map_source_category_group_maps_dairy_group() -> None:
    assert (
        map_source_category_group('Jumbo', 'Zuivel, boter en eieren', None)
        == 'zuivel-boter-en-eieren'
    )


def test_map_source_category_group_maps_produce_group() -> None:
    assert (
        map_source_category_group('Jumbo', 'Aardappelen, groente en fruit', None)
        == 'aardappelen-groente-en-fruit'
    )


def test_map_source_category_group_maps_bread_group_from_category_fallback() -> None:
    assert (
        map_source_category_group('ALDI', None, 'Brood en gebak')
        == 'brood-en-gebak'
    )


def test_map_source_category_returns_none_for_unknown_categories() -> None:
    assert map_source_category('Vomar', None) is None
