import argparse
from utils import load, estimator
import re
import scipy
import nltk
"""
Takes a dataset of N completions and computes correlation between
number of steps in prompt and pass@k
"""
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

def pass_k(df, k):
    if "completion_id" not in df.columns:
        df["completion_id"] = [0]*len(df)
    df_field = df.groupby("__index_level_0__").agg({
        "is_success": "sum", 
        "completion_id": lambda x: max(x) + 1
        }).reset_index()
    df_field = df_field.rename(columns={"is_success":"c","completion_id":"n"})
    df_field["pass@1"] = df_field.apply(lambda x: estimator(x["n"], x["c"], k),axis=1)
    return df_field

def extract_text(prompt):
    prompt = re.split(r"def\s\w+\(\w+\):\n\s+\"\"\"", prompt)[-1].strip()
    return prompt.replace("\"\"\"", "").strip()

def compute_num_verbs(prompt):
    prompt = extract_text(prompt)
    tokens = nltk.word_tokenize(prompt)
    pos_tagged = nltk.pos_tag(tokens)
    verbs = filter(lambda x: x[1].startswith('VB'), pos_tagged)
    return len(list(verbs))

def compute_num_sentences(prompt):
    prompt = extract_text(prompt)
    return len(prompt.split("."))

def main(args):
    ds = load(args.dataset, args.split)
    df = ds.to_pandas()
    print(df["is_success"].mean())

    # compute pass@k
    pass_k_df = pass_k(df, k=1)
    df = df.merge(pass_k_df, on="__index_level_0__")
    print(df)
    print(df["pass@1"].mean())
    
    # compute num steps
    df["num_verbs"] = df["prompt"].apply(compute_num_verbs)
    df["num_sentences"] = df["prompt"].apply(compute_num_sentences)
    # df["num_steps_gpt"] = df["prompt"].apply(compute_num_steps_gpt)
    
    # compute correlation
    verb_corr = scipy.stats.pearsonr(df["num_verbs"], df["pass@1"])
    print(verb_corr)
    sent_corr = scipy.stats.pearsonr(df["num_sentences"], df["pass@1"])
    print(sent_corr)
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("--split", default=None, type=str)
    args = parser.parse_args()
    main(args)
    
"""
PYTESTS
"""

def test_extract_text():
    prompt = '''
def add_up(arr):
    """
    """takes a list of strings, integers, and floats and returns the sum of all the integers and floats."""
    """
    '''
    gold = '''
    takes a list of strings, integers, and floats and returns the sum of all the integers and floats.
    '''.strip()
    output = extract_text(prompt)
    assert output == gold, output
    
def test_compute_num_verbs():
    prompt = '''
def add_up(arr):
    """
    """takes a list of strings, integers, and floats and returns the sum of all the integers and floats."""
    """
    '''
    gold = 2
    output = compute_num_verbs(prompt)
    assert output == gold, output