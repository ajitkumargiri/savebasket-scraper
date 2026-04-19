import json

from typer.testing import CliRunner

from savebasket_data.cli import app

runner = CliRunner()


def test_cli_help_works() -> None:
    result = runner.invoke(app, ['--help'])

    assert result.exit_code == 0
    assert 'SaveBasket data ingestion commands' in result.stdout


def test_demo_normalization_outputs_fixture_summary() -> None:
    result = runner.invoke(app, ['demo-normalization'])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['input_count'] == 10
    assert payload['normalized_count'] == 10
    assert payload['payload_count'] == 4
    assert payload['records'][0]['normalized']['normalized_name'] == 'campina halfvolle melk 1 l'
