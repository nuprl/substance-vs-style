## Building Clues for StudentEval Prompts

# How to use an LLM to determine the clues for a problem.

1. **Build `success_prompts.yaml`**:  
   Subset the StudentEval dataset to only successful prompts. Group by problem.  
   Format each problem group as:

   ```
   prompt_1 \n \n \n ... \n \n prompt_n
   ```

   Save all to the YAML file coupled with the problem name.

2. **Create `template.yaml`**:
   - role: system  
     ...
   - ... few shot examples ...  
   - role: user  
     content: |
     The following prompts all describe the same function:  
     $prompts  
     List the concepts that are common to the majority of the prompts above.


## Annotating Edges

I am using an LLM for data annotation and manually checking/modifying the
results. The results go in a file that looks like this:

```yaml
- template_key1: string
  ...
  template_keyN: string
  _response: string
  _status: "generated" | "accepted" | "modified" | "rejected"
```

On first run, everything is "generated". On a re-run, only rejected is
regenerated. Annotation completes when everything is accepted or rejected.

The prompt template is a YAML file looks like a conversation but uses the
template keys (not _response or _status). For example:

```yaml
- role: system
  content: You are an AI assistant that helps with data annotation.
- role: user
  content: What is the capital of France?
- role: assistant
  content: Paris.
- role: user
  content: What is the capital of $LOCATION?
```