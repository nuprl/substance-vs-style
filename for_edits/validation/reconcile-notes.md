type checking - defer to what they are referring to, regardless of how they actually refer to it
e.g. if they refer to a list as a string erroneously, tag $list:string$ 

word situation

NEVER, EVER TAG $string:character$ of $string:string$ b/c substitution loses precision 

words tags are OK unless it's like "words inside of the string" which is semantically meaningful concept 
also never tag characters when you would have tagged substring 

PROPER STRINGS 
English words
French words
punctionation characters 

TO BE TAGGED CHARACTER, it has to be PLURAL or a SELECTION 

REDO AND DO NOT DO CHARACTERS 

after root[583]['prompt'] we IGNORED CHARACTERS COMPLETELY
BEFORE THAT, we did it, but ignore when doing reconcile 