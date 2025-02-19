from deepdiff import DeepDiff
import yaml 

#first_half = ['Carolyn_annotated_two_of_each_firstlast_firsthalf.yaml', 'two_of_each_firstlast_firsthalf_molly.yaml']
#second_half = ['Carolyn_annotated_two_of_each_firstlast_secondhalf.yaml', 'two_of_each_firstlast_secondhalf_molly.yaml']

#v = ['carolyn_subsetted_firstlast.yaml', 'subsetted_firstlast_molly.yaml']
#v = ['Carolyn_subsetted_firstlast_interim_concensus.yaml', 'subsetted_firstlast_interim_concensus_molly.yaml']
v = ['Carolyn_two_of_each_firstlast_strings_redo.yaml', 'two_of_each_firstlast_strings_redo_molly.yaml']
with open(v[0], 'r') as c:
    carolyn = yaml.safe_load(c)
with open(v[1], 'r') as q:
    molly = yaml.safe_load(q)
diff = DeepDiff(carolyn, molly, verbose_level=1)
#print(diff)
print(diff.pretty())
#print(DeepDiff(carolyn, molly).pretty())
