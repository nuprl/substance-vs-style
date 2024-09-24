from deepdiff import DeepDiff
import yaml 

first_half = ['Carolyn_annotated_two_of_each_firstlast_firsthalf.yaml', 'two_of_each_firstlast_firsthalf_molly.yaml']
second_half = ['Carolyn_annotated_two_of_each_firstlast_secondhalf.yaml', 'two_of_each_firstlast_secondhalf_molly.yaml']

for v in [first_half, second_half]:
    with open(v[0], 'r') as c:
        carolyn = yaml.safe_load(c)
    with open(v[1], 'r') as q:
        molly = yaml.safe_load(q)
    diff = DeepDiff(carolyn, molly, verbose_level=1)
    print(diff)

    #print(diff.pretty())
    #print(DeepDiff(carolyn, molly).pretty())
    print()
    print("***********************")
    print()