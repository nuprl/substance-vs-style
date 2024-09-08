import gradio as gr
from datasets import load_dataset
import argparse
import pandas as pd
from functools import partial
import subprocess
"""
Eventually add filters based on headers
"""
HEADERS = ["__index_level_0__", "problem", "username", "entrypoint", "tests_passed", "total_tests"]
DATATYPES = ["number", "str", "str", "str", "number", "number"]

SUCCESS_HEADERS = ["is_success", "first_attempt","is_first_success", "last_attempt", "is_last_success"]
SUCCESS_DATATYPES = ["bool"]*5

def capture_output(prompt, completion, prints):
    code = "\n".join([prompt, "    "+"   \n".join(completion.split("\n")), prints])
    outputs = subprocess.run(["python", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stderr = gr.Textbox(outputs.stderr.decode("utf-8").strip(), label="Code Errors", type="text")
    stdout = gr.Code(outputs.stdout.decode("utf-8").strip(), label="Code Ouputs", language="python")
    return stderr, stdout

def update_components(
    ds, 
    slider, 
    header_data, 
    success_data, 
    prompt, 
    submitted_text, 
    completion, 
    assertions, 
    prints, 
    code_err, 
    code_output
):
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
    code_err = gr.Textbox("__stderr__", label="Code Errors", type="text")
    code_output = gr.Code("__stdout__", language="python", label="Code Outputs")
    return [slider, header_data, success_data, prompt, submitted_text, 
            completion, assertions, prints, code_err, code_output]
        
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
        
        prompt = gr.Code("__prompt__", language="python", label="Prompt")            
        submitted_text = gr.Textbox("__submitted_text__", type="text", label="Submitted Text")
        completion = gr.Code("__completion__", language="python", label="Completion")
                
        with gr.Row():
            assertions = gr.Code("__assertions__", language="python", label="Assertions")
            prints = gr.Code("__prints__", language="python", label="Prints")
        
        runbtn = gr.Button("Run this code")
        
        with gr.Column():
            with gr.Row():
                code_output = gr.Code("__stdout__", language="python", label="Code Outputs")
                code_err = gr.Textbox("__stderr__", label="Code Errors", type="text")
        
        gr.Markdown("**Logging and Filtering**\n")
        with gr.Column():
            with gr.Row():
                flagbtn = gr.Button("Flag this example to log file")
                flagout = gr.Textbox(label="Num examples in logfile")
            
        # updates                
        # run code
        runbtn.click(fn=capture_output, inputs=[prompt, completion, prints], outputs=[code_err,code_output])
        # change example on slider change
        components = [slider, header_data, success_data, prompt, submitted_text, completion, assertions, prints, code_err, code_output]
        slider.input(fn=partial(update_components, ds), inputs=components, outputs=components)
        # log
        callback.setup(components, "flagged_data_points")
        flagbtn.click(lambda *args: callback.flag(list(args)), components, flagout,
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
