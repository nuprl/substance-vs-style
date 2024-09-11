from datasets import load_from_disk, load_dataset
import os
import numpy as np

def load(dataset, split):
    if os.path.exists(dataset):
        ds = load_from_disk(dataset)
    else:
        ds = load_dataset(dataset)
        
    if split:
        ds = ds[split]
    return ds
    

# from Multipl-E
def estimator(n: int, c: int, k: int) -> float:
    """
    Calculates 1 - comb(n - c, k) / comb(n, k).
    """
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))