import pytest

from app import day1_data


@pytest.mark.parametrize('command', ['import', 'validate'])
def test_cli_reports_failed_validation_as_nonzero(monkeypatch, capsys, command):
    from contextlib import nullcontext

    results = [{'status': 'FAIL', 'check_name': 'example', 'details': {}}]
    monkeypatch.setattr('sys.argv', ['day1_data', command])
    monkeypatch.setattr(day1_data, '_session_factory', lambda: lambda: nullcontext(None))
    monkeypatch.setattr(day1_data, 'validate_day1_data', lambda db: results)
    monkeypatch.setattr(day1_data, 'import_day1_data', lambda: {'validation_results': results})
    monkeypatch.setattr(day1_data, 'print_report', lambda report: print('FAIL example'))
    with pytest.raises(SystemExit) as error:
        day1_data.main()
    assert error.value.code == 1
    assert 'FAIL example' in capsys.readouterr().out
