"""Property-based (Hypothesis) and parser-fuzzing (atheris-compatible) checks for KS Lab."""
import json
import math
import random
import unittest

try:
    from hypothesis import given, settings, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


def dot_int(u: list[int], v: list[int]) -> int:
    return sum(a * b for a, b in zip(u, v))


def normalize_ray(v: list[int]) -> tuple[int, ...] | None:
    if all(x == 0 for x in v):
        return None
    g = 0
    for x in v:
        g = math.gcd(g, abs(x))
    w = [x // g for x in v]
    for x in w:
        if x != 0:
            if x < 0:
                w = [-y for y in w]
            break
    return tuple(w)


def fuzz_drup_header(raw: bytes) -> None:
    """Atheris-compatible fuzz target for malformed DIMACS/DRUP/JSON bytes."""
    try:
        text = raw.decode("utf-8", errors="strict")
        if text.startswith("{"):
            json.loads(text)
        else:
            for line in text.splitlines()[:20]:
                parts = line.split()
                if parts and parts[0] not in ("c", "p", "d"):
                    [int(x) for x in parts]
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError, RecursionError):
        return


class KSPropertyAndFuzzTests(unittest.TestCase):
    def _check_ray_invariants(self, v: list[int], scale: int) -> None:
        r1 = normalize_ray(v)
        r2 = normalize_ray([scale * x for x in v])
        self.assertEqual(r1, r2)
        if r1 is not None:
            self.assertEqual(normalize_ray(list(r1)), r1)
            nz = [x for x in r1 if x != 0]
            self.assertGreater(nz[0], 0)

    if HAS_HYPOTHESIS:
        @given(
            v=st.lists(st.integers(min_value=-4, max_value=4), min_size=3, max_size=5),
            scale=st.integers(min_value=-5, max_value=5).filter(lambda x: x != 0),
        )
        @settings(max_examples=200, derandomize=True)
        def test_ray_normalization_invariants(self, v: list[int], scale: int) -> None:
            self._check_ray_invariants(v, scale)
    else:
        def test_ray_normalization_invariants_fallback(self) -> None:
            rng = random.Random(20261124)
            for _ in range(200):
                d = rng.randint(3, 5)
                v = [rng.randint(-4, 4) for _ in range(d)]
                scale = rng.choice([-3, -2, -1, 1, 2, 3])
                self._check_ray_invariants(v, scale)

    def test_fuzz_corpus(self) -> None:
        rng = random.Random(20261124)
        for _ in range(200):
            fuzz_drup_header(bytes(rng.getrandbits(8) for _ in range(rng.randint(0, 80))))


if __name__ == "__main__":
    unittest.main()
