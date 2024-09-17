import argparse
from utils import load, estimator
import re
import scipy
import nltk
import spacy
from spacy.pipeline import DependencyParser
from spacy.pipeline.dep_parser import DEFAULT_PARSER_MODEL
import en_core_web_sm
from multiprocessing import cpu_count
import string
import matplotlib.pyplot as plt
"""
Takes a dataset of N completions and computes correlation between
number of steps in prompt and pass@k
"""
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
nlp = en_core_web_sm.load()
dep_parser = nlp.get_pipe("parser")

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

def compute_num_verbs_nltk(prompt):
    prompt = extract_text(prompt)
    tokens = nltk.word_tokenize(prompt)
    pos_tagged = nltk.pos_tag(tokens)
    verbs = filter(lambda x: x[1].startswith('VB'), pos_tagged)
    return len(list(verbs))

def compute_num_verbs_spacy(prompt):
    """
    uses dependency parsing
    """
    prompt = extract_text(prompt)
    doc = nlp(prompt)
    processed = dep_parser(doc)
    num_verbs = 0
    for token in processed:
        if token.dep_ in ["ROOT","conj"]:
            # these are problem specific exceptions: generateCardDeck, getSeason, convert
            # where dep parsing fails
            if not (token.text.lower() in
                ["winter","spring","summer","fall","autumn"] 
                + [str(num) for num in range(26)] 
                + [str(chr(97+i)) for i in range(26)]
                + list(string.punctuation)
            ):
                num_verbs += 1
    return num_verbs

def compute_num_sentences(prompt):
    prompt = extract_text(prompt)
    return len(prompt.split("."))

def plot_columns(df, x_col, y_col, title=None, xlabel=None, ylabel=None, color='blue', marker='o'):
    """
    Create a scatter plot of column x_col against column y_col in the given DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data.
    - x_col (str): The name of the column to be used for the x-axis.
    - y_col (str): The name of the column to be used for the y-axis.
    - title (str): Title of the plot. Default is None.
    - xlabel (str): Label for the x-axis. Default is None.
    - ylabel (str): Label for the y-axis. Default is None.
    - color (str): Color of the scatter points. Default is 'blue'.
    - marker (str): Marker style for the scatter points. Default is 'o'.
    """
    plt.figure(figsize=(10, 6))
    
    # Create scatter plot
    plt.scatter(df[x_col], df[y_col], color=color, marker=marker)
    
    # Set plot title and labels
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    
    plt.grid(True)

def main(args):
    ds = load(args.dataset, args.split)
    # compute num steps
    ds = ds.map(lambda x: {**x, 
                           "num_verbs": compute_num_verbs_spacy(x["prompt"]),
                           "num_sentences": compute_num_sentences(x["prompt"]),
                           "prompt_len": len(x["prompt"]),
                           #"num_steps_gpt": compute_num_steps_gpt(x["prompt"])
                }, num_proc=cpu_count(), desc="Computing num steps")
    ds = ds.filter(lambda x: not "def " in x["prompt"].split(":", 1)[-1], num_proc=cpu_count(), desc="Filtering bad prompts")
    df = ds.to_pandas()
    print(ds)

    # compute pass@k
    pass_k_df = pass_k(df, k=1)
    df = df.merge(pass_k_df, on="__index_level_0__")
    print("Pass@1:", df["pass@1"].mean())
    
    df = df.sort_values(by="num_verbs")
    df.to_csv(args.outcsv)
    print(df)
    # print distribution of num verbs
    print(df["num_verbs"].value_counts())
    
    # compute correlation
    verb_corr = scipy.stats.pearsonr(df["num_verbs"], df["pass@1"])
    print(verb_corr)
    
    # plot pass@k against num_verb
    plot_columns(df, "pass@1", "num_verbs",xlabel="pass@1", ylabel="num_verbs")
    plt.savefig(args.outcsv.replace(".csv", ".pdf"))
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outcsv")
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
    
def test_compute_num_verbs_nltk():
    prompt = '''
def add_up(arr):
    """
    """From the first list of parameters, the function $takes$ the last element first and $goes$ backwards 
    towards the first element. It $attaches$ these elements with the inputs given in the second list. 
    A new list is $made$ which is appended continuously with these new attachments. No function is 
    $called$ for this but rather the two stings which are to be attached are $concatenated$. 
    During concatenation, the element of the first list is $put$ first and the element of the second 
    list is $put$ second. The suit $comes$ first and then $comes$ the val for every concatenation. And the suits 
    list $starts$ from backwards. This $goes$ on until the elements of the first list are exhausted."""
    """'''
    gold = len(re.findall(r"\$\w+\$", prompt))
    # output = compute_num_verbs_nltk(prompt.replace("$",""))
    output = compute_num_verbs_spacy(prompt.replace("$",""))
    assert output == gold, output