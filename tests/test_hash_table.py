import unittest

from src.hash_table import HashTable, LinearProbingHashTable


class ChainedHashTableTests(unittest.TestCase):
    def test_collisions_updates_search_and_delete(self):
        table = HashTable(capacity=8)
        table.insert("a", 1)
        table.insert("i", 2)

        self.assertEqual(table.search("a"), 1)
        self.assertEqual(table.search("i"), 2)
        self.assertEqual(table.last_probes, 2)
        table.insert("a", 3)
        self.assertEqual(len(table), 2)
        self.assertEqual(table.search("a"), 3)
        self.assertTrue(table.delete("a"))
        self.assertFalse(table.delete("missing"))
        self.assertEqual(table.search("a"), None)

    def test_capacity_and_key_validation(self):
        for capacity in (0, -1, True):
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    HashTable(capacity=capacity)
        table = HashTable(capacity=3)
        with self.assertRaises(TypeError):
            table.insert(1, "value")


class LinearProbingHashTableTests(unittest.TestCase):
    def test_collision_wraps_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(capacity=5)
        table.insert("c", 1)  # ord("c") % 5 == 4
        table.insert("h", 2)  # Same home slot; wraps to slot zero.

        self.assertEqual(table.items_at(4), (("c", 1),))
        self.assertEqual(table.items_at(0), (("h", 2),))
        self.assertEqual(table.probe_path("h"), (4, 0))
        self.assertEqual(table.search("h"), 2)
        self.assertEqual(table.last_probes, 2)

    def test_full_table_fails_and_deleted_slot_is_reusable(self):
        table = LinearProbingHashTable(capacity=2)
        table.insert("a", 1)
        table.insert("b", 2)
        with self.assertRaises(OverflowError):
            table.insert("c", 3)
        self.assertTrue(table.delete("a"))
        self.assertEqual(table.search("b"), 2)
        table.insert("c", 3)
        self.assertEqual(table.search("c"), 3)

    def test_overwrite_does_not_add_duplicate(self):
        table = LinearProbingHashTable(capacity=3)
        table.insert("a", 1)
        table.insert("a", 2)
        self.assertEqual(len(table), 1)
        self.assertEqual(table.search("a"), 2)


if __name__ == "__main__":
    unittest.main()
