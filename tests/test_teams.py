from teams import assign_role, calculate_team_readiness, create_team


def test_create_team() -> None:
    teams: dict[str, dict] = {}
    assert create_team(teams, "Альфа", "Журнал") is True
    assert create_team(teams, "Альфа", "Журнал") is False


def test_assign_role() -> None:
    team = {"students": {"Анна": {"role": "не назначена"}}}
    assert assign_role(team, "Анна", "аналитик") is True
    assert team["students"]["Анна"]["role"] == "аналитик"


def test_calculate_team_readiness() -> None:
    team = {
        "students": {
            "Анна": {"role": "аналитик"},
            "Борис": {"role": "разработчик"},
            "Вера": {"role": "тестировщик"},
        }
    }
    assert calculate_team_readiness(team) == (100, "Команда готова к работе")
