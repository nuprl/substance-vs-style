To build:

```bash
CD REPO_ROOT
for F in tagging_clues/tagging_graphs_oct9_trimmed/*.yaml; do python3 alternating_automata.py --render $F; done
cd tagging_clues/dots
mv ../tagging_graphs_oct9_trimmed/*.pdf .
rm ../tagging_graphs_oct9_trimmed/*.dot
```