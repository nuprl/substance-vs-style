import gradio as gr
import argparse
import pandas as pd
from functools import partial
import subprocess
from utils import load
"""
Eventually add filters based on headers
"""
HEADERS = ["__index_level_0__", "problem", "username", "tests_passed", "total_tests"]
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
    if isinstance(ds, gr.State):
        ds = ds.value
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
    row = row.iloc[0]
    prompt = gr.Code(row["prompt"], language="python", label="Prompt")
    submitted_text = gr.Textbox(row["prompt"]+row["completion"], type="text", label="Submitted Text")
    completion = gr.Code(row["completion"], language="python", label="Completion")
    assertions = gr.Code(row["assertions"], language="python", label="Assertions")
    prints = gr.Code(row["prints"], language="python", label="Prints")
    code_err = gr.Textbox("__stderr__", label="Code Errors", type="text")
    code_output = gr.Code("__stdout__", language="python", label="Code Outputs")
    slider = gr.Slider(0, len(ds) - 1, step=1, label="Problem ID (click and arrow keys to navigate):", value=slider)
    return [slider, header_data, success_data, prompt, submitted_text, 
            completion, assertions, prints, code_err, code_output]

def filter_by(
    dataset_name, 
    dataset_split,
    fs_box, ls_box, ff_box, lf_box, f_box, l_box, is_success_box, is_failure_box, 
    problem_box,
    student_box,
    slider,
    *components_to_update):
    ds = load(dataset_name, split=dataset_split)
    success_boxes = [fs_box, ls_box, ff_box, lf_box, f_box, l_box, is_success_box]
    ds = ds.to_pandas()
    labels = ["is_first_success","is_last_success","is_first_failure","is_last_failure",
              "first_attempt","last_attempt","is_success"]
    for label, box in zip(labels, success_boxes):
        if box:
            ds = ds[ds[label] == box]
    
    if is_failure_box != None:
        ds = ds[ds["is_success"] == box]
            
    if problem_box != None:
        ds = ds[ds["problem"] == problem_box]
        
    if student_box != None:
        ds = ds[ds["username"] == student_box]
    
    dataset = gr.State(ds)
    return [dataset, *update_components(ds, 0, *components_to_update)]
        
def main(args):
    ds = load(args.dataset,args.split)
    ds = ds.to_pandas()    
    callback = gr.SimpleCSVLogger()
    student_usernames = list(set(ds["username"]))
    student_usernames.sort(key=lambda x: int(x.replace("student","")))
    problem_names = list(set(ds["problem"]))
    problem_names.sort()
    
    with gr.Blocks(theme="gradio/monochrome") as demo:
        dataset = gr.State(ds)
        # slider for selecting problem id
        slider = gr.Slider(0, len(ds) - 1, step=1, label="Problem ID (click and arrow keys to navigate):")
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
        
        gr.Markdown("**Logging**\n")
        with gr.Column():
            with gr.Row():
                flagbtn = gr.Button("Flag this example to log file")
                flagout = gr.Textbox(label="Num examples in logfile")
            
        # updates                
        # run code
        runbtn.click(fn=capture_output, inputs=[prompt, completion, prints], outputs=[code_err,code_output])
        # change example on slider change
        components = [slider, header_data, success_data, prompt, submitted_text, completion, assertions, prints, code_err, code_output]
        slider.input(fn=update_components, inputs=[dataset, *components], outputs=components)
        # log
        callback.setup(components, "flagged_data_points")
        flagbtn.click(lambda *args: callback.flag(list(args)), components, flagout,
                  preprocess=False, show_progress="full", trigger_mode="once")

        # add filtering options
        gr.Markdown("**Filtering (reload to clear all filters)**\n")
        with gr.Row():
            with gr.Column():
                fs_box = gr.Checkbox(label="is_first_success")
                ls_box = gr.Checkbox(label="is_last_success")
            with gr.Column():
                ff_box = gr.Checkbox(label="is_first_failure")
                lf_box = gr.Checkbox(label="is_last_failure")
            with gr.Column():
                f_box = gr.Checkbox(label="first_attempt")
                l_box = gr.Checkbox(label="last_attempt")
            with gr.Column():
                is_success_box = gr.Checkbox(label="is_success")
                is_failure_box = gr.Checkbox(label="is_failure", value=False)
            success_boxes = [fs_box, ls_box, ff_box, lf_box, f_box, l_box, is_success_box, is_failure_box]
            problem_box = gr.Dropdown(label="problem", choices = problem_names)
            student_box = gr.Dropdown(label="username", choices = student_usernames)
            filter_btn = gr.Button("Filter")
        
        filter_btn.click(fn=partial(filter_by, args.dataset, args.split), inputs=[*success_boxes, problem_box, student_box, *components], 
                         outputs=[dataset, *components])

    demo.launch(share=args.share)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=str, default="wellesley-easel/StudentEval")
    parser.add_argument("--split", type=str, default=None)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()
    main(args)
