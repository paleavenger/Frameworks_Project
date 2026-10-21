from utils import same_name


def test_same_name() -> None:
    assert same_name(" Анна ", "анна")
    assert not same_name("Анна", "Борис")
