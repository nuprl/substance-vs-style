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