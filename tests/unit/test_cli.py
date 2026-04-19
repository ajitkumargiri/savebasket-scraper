from typer.testing import CliRunner

from savebasket_data.cli import app


def test_cli_help_works() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "SaveBasket data ingestion commands" in result.stdout
