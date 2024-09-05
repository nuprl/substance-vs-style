import gradio as gr
from datasets import load_dataset
import argparse
import pandas as pd
from functools import partial
"""
Eventually add filters based on headers
slider for selecting problem id, code and arrow
"""
HEADERS = ["__index_level_0__", "problem", "username", "entrypoint", "tests_passed", "total_tests"]
DATATYPES = ["number", "str", "str", "str", "number", "number"]

SUCCESS_HEADERS = ["is_success", "first_attempt","is_first_success", "last_attempt", "is_last_success"]
SUCCESS_DATATYPES = ["bool"]*5

def update_components(ds, slider, header_data, success_data, prompt, submitted_text, completion, assertions, prints):
    row = ds.iloc[[slider]]
    header_data = gr.Dataframe(
        headers=HEADERS,
        datatype=DATATYPES,
        row_count=1,
        col_count=(len(HEADERS), "fixed"),
        column_widths=["60px"]*len(HEADERS),
        value=row[HEADERS],
        interactive=False
    )
    success_data = gr.Dataframe(
        headers=SUCCESS_HEADERS,
        datatype=SUCCESS_DATATYPES,
        row_count=1,
        col_count=(len(SUCCESS_HEADERS), "fixed"),
        column_widths=["60px"]*len(SUCCESS_HEADERS),
        value=row[SUCCESS_HEADERS],
        interactive=False
    )
    row = ds.iloc[slider]
    prompt = gr.Code(row["prompt"], language="python", label="Prompt")
    submitted_text = gr.Textbox(row["submitted_text"], type="text", label="Submitted Text")
    completion = gr.Code(row["completion"], language="python", label="Completion")
    assertions = gr.Code(row["assertions"], language="python", label="Assertions")
    prints = gr.Code(row["prints"], language="python", label="Prints")
    return slider, header_data, success_data, prompt, submitted_text, completion, assertions, prints
        
def main(args):
    ds = pd.read_parquet("hf://datasets/wellesley-easel/StudentEval/data/test-00000-of-00001.parquet")
    
    callback = gr.SimpleCSVLogger()

    with gr.Blocks(theme="gradio/monochrome") as demo:
        # slider for selecting problem id
        slider = gr.Slider(0, len(ds), step=1, label="Problem ID (click and arrow keys to navigate):")
        # display headers in dataframe for problem id
        header_data = gr.Dataframe(
            headers=HEADERS,
            datatype=DATATYPES,
            row_count=1,
            col_count=(len(HEADERS), "fixed"),
            column_widths=["60px"]*len(HEADERS),
            interactive=False,
        )
        success_data = gr.Dataframe(
            headers=SUCCESS_HEADERS,
            datatype=SUCCESS_DATATYPES,
            row_count=1,
            col_count=(len(SUCCESS_HEADERS), "fixed"),
            column_widths=["60px"]*len(SUCCESS_HEADERS),
            interactive=False,
        )
        
        # display submitted text for problem id
        prompt = gr.Code("__prompt__", language="python", label="Prompt")            

        # display prompt for problem id
        submitted_text = gr.Textbox("__submitted_text__", type="text", label="Submitted Text")
                
        # display completion for problem id
        completion = gr.Code("__completion__", language="python", label="Completion")
                
        with gr.Row():
            assertions = gr.Code("__assertions__", language="python", label="Assertions")
            prints = gr.Code("__prints__", language="python", label="Prints")
        
        # on slider change, update all data
        components = [slider, header_data, success_data, prompt, submitted_text, completion, assertions, prints]
        # This needs to be called at some point prior to the first call to callback.flag()
 
        slider.input(fn=partial(update_components, ds), inputs=components, outputs=components)
        
        gr.Markdown("**Logging and Filtering**\n")
        with gr.Column():
            with gr.Row():
                btn = gr.Button("Flag this example to log file")
                out = gr.Textbox(label="Num examples in logfile")
            
        callback.setup(components, "flagged_data_points")
        btn.click(lambda *args: callback.flag(list(args)), components, out,
                  preprocess=False, show_progress="full", trigger_mode="once")
        
        # TODO: add filtering options
        
        
    demo.launch(share=args.share)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="wellesley-easel/StudentEval")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()
    main(args)
