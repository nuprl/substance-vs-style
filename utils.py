from datasets import load_from_disk, load_dataset, Dataset
import os
import numpy as np
from typing import List

def load(dataset, split):
    if os.path.exists(dataset):
        ds = load_from_disk(dataset)
    else:
        ds = load_dataset(dataset)
        
    if split:
        ds = ds[split]
    return ds
    
def dedup_by_fields(ds: Dataset, fields: List[str]):
    ds = ds.map(lambda x: {**x, "__field__": " ".join([x[y] for y in fields])})
    seen = set()
    new_ds = []
    for item in ds:
        if item["__field__"] not in seen:
            field = item.pop("__field__")
            seen.add(field)
            new_ds.append(item)
    return Dataset.from_list(new_ds)

# from Multipl-E
def estimator(n: int, c: int, k: int) -> float:
    """
    Calculates 1 - comb(n - c, k) / comb(n, k).
    """
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))