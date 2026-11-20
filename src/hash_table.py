"""Fixed-capacity hash tables for the URL shortener exercises."""

class _DeletedSlot:
    pass


_DELETED = _DeletedSlot()


def horner_hash(key: str) -> int:
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    value = 0
    for character in key:
        value = value * 31 + ord(character)
    return value


class HashTable:
    """A hash table using separate chaining and a polynomial Horner hash."""

    def __init__(self, capacity: int = 101):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self._capacity = capacity
        self._buckets: list[list[tuple[str, object]]] = [
            [] for _ in range(capacity)
        ]
        self._size = 0
        self.last_probes = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def hash_details(self, key: str) -> tuple[int, int]:
        value = horner_hash(key)
        return value, value % self._capacity

    def probe_path(self, key: str) -> tuple[int, ...]:
        _, index = self.hash_details(key)
        return (index,)

    def items_at(self, index: int) -> tuple[tuple[str, object], ...]:
        if not 0 <= index < self._capacity:
            raise IndexError("table index out of range")
        return tuple(self._buckets[index])

    def insert(self, key: str, value: object) -> None:
        _, index = self.hash_details(key)
        bucket = self._buckets[index]
        for position, (stored_key, _) in enumerate(bucket):
            self.last_probes = position + 1
            if stored_key == key:
                bucket[position] = (key, value)
                return
        bucket.append((key, value))
        self.last_probes = len(bucket)
        self._size += 1

    def search(self, key: str) -> object | None:
        _, index = self.hash_details(key)
        bucket = self._buckets[index]
        for position, (stored_key, value) in enumerate(bucket):
            self.last_probes = position + 1
            if stored_key == key:
                return value
        self.last_probes = len(bucket)
        return None

    def delete(self, key: str) -> bool:
        _, index = self.hash_details(key)
        bucket = self._buckets[index]
        for position, (stored_key, _) in enumerate(bucket):
            self.last_probes = position + 1
            if stored_key == key:
                del bucket[position]
                self._size -= 1
                return True
        self.last_probes = len(bucket)
        return False

    def __len__(self) -> int:
        return self._size


class LinearProbingHashTable(HashTable):
    """A fixed-capacity hash table using linear probing."""

    def __init__(self, capacity: int = 101):
        super().__init__(capacity)
        self._slots: list[tuple[str, object] | _DeletedSlot | None] = [
            None for _ in range(capacity)
        ]

    def items_at(self, index: int) -> tuple[tuple[str, object], ...]:
        if not 0 <= index < self._capacity:
            raise IndexError("table index out of range")
        slot = self._slots[index]
        if not isinstance(slot, tuple):
            return ()
        return (slot,)

    def probe_path(self, key: str) -> tuple[int, ...]:
        _, start = self.hash_details(key)
        path = []
        for offset in range(self._capacity):
            index = (start + offset) % self._capacity
            path.append(index)
            slot = self._slots[index]
            if slot is None:
                break
            if isinstance(slot, tuple) and slot[0] == key:
                break
        return tuple(path)

    def insert(self, key: str, value: object) -> None:
        _, start = self.hash_details(key)
        first_deleted = None
        for offset in range(self._capacity):
            index = (start + offset) % self._capacity
            slot = self._slots[index]
            self.last_probes = offset + 1
            if slot is None:
                target = first_deleted if first_deleted is not None else index
                self._slots[target] = (key, value)
                self._size += 1
                return
            if slot is _DELETED:
                if first_deleted is None:
                    first_deleted = index
            elif isinstance(slot, tuple) and slot[0] == key:
                self._slots[index] = (key, value)
                return

        if first_deleted is not None:
            self._slots[first_deleted] = (key, value)
            self._size += 1
            return
        raise OverflowError("linear-probing hash table is full")

    def search(self, key: str) -> object | None:
        _, start = self.hash_details(key)
        for offset in range(self._capacity):
            index = (start + offset) % self._capacity
            slot = self._slots[index]
            self.last_probes = offset + 1
            if slot is None:
                return None
            if isinstance(slot, tuple) and slot[0] == key:
                return slot[1]
        return None

    def delete(self, key: str) -> bool:
        _, start = self.hash_details(key)
        for offset in range(self._capacity):
            index = (start + offset) % self._capacity
            slot = self._slots[index]
            self.last_probes = offset + 1
            if slot is None:
                return False
            if isinstance(slot, tuple) and slot[0] == key:
                self._slots[index] = _DELETED
                self._size -= 1
                return True
        return False
