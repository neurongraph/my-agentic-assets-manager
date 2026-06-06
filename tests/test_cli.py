from typer.testing import CliRunner
from maam.cli.app import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "MAAM version: 0.1.0" in result.output

def test_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "MAAM Doctor" in result.output
    assert "MAAM home" in result.output
    assert "healthy" in result.output

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MAAM" in result.output
