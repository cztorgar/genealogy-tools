"""Registr modulů. Nový modul = soubor v tomto balíčku s třídou a řádek níže."""

from .aron_zamrsk import AronZamrsk

MODULES = {
    AronZamrsk.id: AronZamrsk,
}

_instances: dict = {}


def get(module_id: str):
    if module_id not in MODULES:
        raise KeyError(f"neznámý modul {module_id!r}; dostupné: {', '.join(MODULES)}")
    if module_id not in _instances:
        _instances[module_id] = MODULES[module_id]()
    return _instances[module_id]
