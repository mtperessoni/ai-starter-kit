"""In-memory repositories and the global state reset used by every test."""
from market.infra import clock, config, events, ids
from market.infra.errors import NotFoundError, ValidationError


class InMemoryRepository:
    def __init__(self, name: str = "") -> None:
        self.name = name
        self._items: dict = {}

    def add(self, key, obj) -> None:
        if key in self._items:
            raise ValidationError(f"{self.name}: duplicate key {key}")
        self._items[key] = obj

    def get(self, key):
        if key not in self._items:
            raise NotFoundError(f"{self.name}: {key} not found")
        return self._items[key]

    def find(self, key):
        return self._items.get(key)

    def save(self, key, obj) -> None:
        self._items[key] = obj

    def delete(self, key) -> None:
        self._items.pop(key, None)

    def all(self) -> list:
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()


_repos: dict[str, InMemoryRepository] = {}


def repo(name: str) -> InMemoryRepository:
    if name not in _repos:
        _repos[name] = InMemoryRepository(name)
    return _repos[name]


def reset_all() -> None:
    for repository in _repos.values():
        repository.clear()
    ids.reset()
    config.reset()
    clock.reset()
    events.reset_history()
