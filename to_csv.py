import sys
from utils import load
import pandas as pd

ds = sys.argv[1]
split = sys.argv[2]
outcsv = sys.argv[3]

ds = load(ds, split=split)
df = ds.to_pandas()
df.to_csv(outcsv)