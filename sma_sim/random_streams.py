from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping

import numpy as np
from scipy import stats


DEFAULT_STREAM_NAMES = (
    "elective_calls",
    "urgent_arrivals",
    "no_shows",
    "punctuality",
    "elective_durations",
    "urgent_scan_type",
    "urgent_durations",
)


def stable_seed(base_seed: int, replication: int, stream_name: str) -> int:
    token = f"{base_seed}:{replication}:{stream_name}".encode("utf-8")
    digest = hashlib.blake2b(token, digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big") % (2**32 - 1)


def make_stream_seeds(
    base_seed: int,
    replication: int,
    stream_names: Iterable[str] = DEFAULT_STREAM_NAMES,
) -> Dict[str, int]:
    return {name: stable_seed(base_seed, replication, name) for name in stream_names}


@dataclass
class RandomStreams:
    base_seed: int
    replication: int
    antithetic: bool = False
    stream_names: Iterable[str] = DEFAULT_STREAM_NAMES
    seeds: Mapping[str, int] = field(init=False)
    generators: Dict[str, np.random.Generator] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "seeds",
            make_stream_seeds(self.base_seed, self.replication, self.stream_names),
        )
        object.__setattr__(
            self,
            "generators",
            {name: np.random.default_rng(seed) for name, seed in self.seeds.items()},
        )

    def uniform(self, stream_name: str) -> float:
        u = float(self.generators[stream_name].random())
        if self.antithetic:
            u = 1.0 - u
        return min(max(u, 1e-12), 1.0 - 1e-12)

    def exponential_minutes(self, stream_name: str, expected_count: float, horizon_minutes: float) -> float:
        if expected_count <= 0:
            raise ValueError("expected_count must be positive")
        mean_minutes = horizon_minutes / expected_count
        return -np.log(1.0 - self.uniform(stream_name)) * mean_minutes

    def normal(self, stream_name: str, mean: float, sd: float) -> float:
        return float(stats.norm.ppf(self.uniform(stream_name), loc=mean, scale=sd))

    def positive_normal(self, stream_name: str, mean: float, sd: float) -> float:
        lower_cdf = stats.norm.cdf(0.0, loc=mean, scale=sd)
        u = lower_cdf + self.uniform(stream_name) * (1.0 - lower_cdf)
        return float(stats.norm.ppf(u, loc=mean, scale=sd))

    def bernoulli(self, stream_name: str, probability: float) -> bool:
        return self.uniform(stream_name) < probability

    def categorical(self, stream_name: str, probabilities: Iterable[float]) -> int:
        u = self.uniform(stream_name)
        cumulative = 0.0
        last_idx = 0
        for idx, probability in enumerate(probabilities):
            cumulative += float(probability)
            last_idx = idx
            if u <= cumulative:
                return idx
        return last_idx

