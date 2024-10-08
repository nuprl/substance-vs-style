
SUCCESS_CLUES = {
    "add_up": [1,2,3,4,5],
    "add_int": [1,2,3,4],
    "topScores": [1,2,3,4,5,6],
    "total_bill": [1,2,3,4,5,6,7,8],
    "laugh": [1,2,3,4,5,6],
    "translate": [1,2,3,4,5,6,7],
    "fib": [1,2,3],
    "assessVowels": [1,2,3,4],
    "planets_mass": [1,2,3,4,5,6],
    "altText": [1,2,3,4],
    "readingIceCream": [1,2,3,4,5,6,7],
    "changeSection": [1,2,3,4],
    "subtract_add": [1,2,3,4,5],
    "increaseScore": [1,2,3,4,6],
    "percentWin": [1,2,3,4,5,6],
    "pattern": [1,2,3,4,5],
    "times_with": [1,2,3,4,5],
    "student_grades": [1,2,3,4],
    "sortedBooks": [1,2,3,4,5,6],
    "sort_physicists": [1,2,3,4,5,6],
    "sortBySuccessRate": [1,2,3,4,5,6],
    "set_chars": [1,2,3,4,5],
    "reverseWords": [1,2,3,4,5],
    "remove_odd": [1,2,3,4],
    "print_time": [1,2,3,4,5],
    "getSeason": [1,2,3,4],
    "generateCardDeck": [1,2,3,4,5],
    "find_multiples": [1,2],
    "findHorizontals": [1,2,3,4,5,6]
}

KNOWN_EXCEPTIONS = {
    #arya
    # student12, 77 special cases. "2nd index": indexing ambiguity + trivial success
    "sort_physicists": {
        "success": {
            "student12": {
                3: "student should be awarded clue 2 in start clues"
            }
        },
        "fail": {
            "student19": {
                1: "Model runs out of tokens"
            }
        },
        "neutral": {
            "student20": {
                2: "first index versus index 1: zero-indexing ambiguity"
            },
            "student36": {
                1: "model ignores filter by physics",
                2: "model ignores sort by key1, does sort because inability to lookback and get key1 after filtering"
            },
            "student77": {
                2: "model ignores instruction to only return the scientist. model should understand it means name",
                3: "model lookback error, same as student36.2",
                4: "same as previous attempt"
            }
        },
        "cycles": {
            "student77": {
                2: "these are two cycles, technically this is a breakout edge",
                4: "this is a trivial edit; lookback error is the problem here" 
            }
        },
        "breakout": {
            "student12": {
                3: "student is technically incorrect, but due to lacking test coverage, passes"
            },
            "student57": {
                2: "same as student12"
            },
            "student77": {
                5: "same as student12"
            }
        }
    },
    "find_multiples": {
        "success": {
            "student22": {
                3: "model infers clue 1 from func signature"
            },
            "student5": {
                1: "model infers correct answer from func signature though prompt is wrong"
            },
            "student74": {
                1: "model infers correct answer from func signature though prompt is wrong"
            }
        },
        "breakout": {
            "student11": {
                3: "missing same clue as loop"
            }
        }

    },
    # fran
    "add_int": {
        # false success, does not have all clues but is success
        "success": {
            # username: {attempt_id: exception reason}
            "student19": {1: "clue 1 optional, but more efficient"},
            "student36": {1: "clue 1 optional, but more efficient"},
            "student54": {4: "clue 1 optional, but more efficient - student has long path to success"}
        },
        # false neutral, should be success because has all clues
        "neutral": {
            "student38": {1: "marked as neutral because not last attempt, but successful",
                        2: "this attempt follows a previous success"},
        },
        # false fail, should be success because all clues
        "fail": {
            "student38": {3: "this final attempt follows a previous success"},
        }
    },
    "add_up": {
        "success": {
            "student24": {1: """incomplete clues is successful due to use of python try-except
                          (student mentions 'error' in prompt)"""}
        },
        "fail":{
            "student65": {5: "has all clues, but still fails because model interprets 'number' as int"}
        },
        "breakout": {
            "student31":{
                2: "student only has 2 attempts; incomplete data"
            },
            "student47":{
                5: "breakout edge leads into another cycle"
            },
            "student65": {
                5: "breakout edge leads to final node; could be another cycle"
            }
        }
    },
    "topScores": {
        "success": {},
        "neutral": {
            "student45": {1:"student with all clues gets fail because of LLM runs out of tokens",
                          2:"same as previous attempt",
                          3:"same as previous attempt",
                          4:"same as previous attempt",
                          5:"same as previous attempt",
                          6:"same as previous attempt"},
            "student53": {4: """student has all clues; wording leads to LLM fail. Good example to highlight,
                          since student eventually gets it right. What did they change? Got rid of 'lookback'
                          statements""",
                          6: "same as previous attempt",
                          7: "same as previous attempt",
                          8: "same as previous attempt",
                          9: "same as previous attempt"
                          }
        },
        "fail": {
            "student45": {7:"student with all clues gets fail because of LLM runs out of tokens"}
        },
        "cycles": {
            "student45": {
                3: "student with all clues gets fail because of LLM runs out of tokens",
                4: "same as previous attempt"
            },
        },
        "breakout": {
            "student15": {
                10: "Student breaks out into another cycle",
            },
            "student53": {
                10: "LLM runs out of tokens error in node_from. Should have been a success from attempt 7"
            }
        }
    },
    # Carolyn
    "findHorizontals": {
        "breakout": {
            "student70": {
                3: "student fails, could be cont cycle"
            }
        }
    },
    "generateCardDeck": {
        "success": {
            "student33": {
                1: "missing clue 3,5. 5 implicit, 4 can be implicit in this case"
            },
            "student60":{
                5: "missing clue 5 is implicit"
            },
            "student63": {
                1: "missing clue 1 is implicit. 4 can be implicit in this case"
            },
            "student64": {
                7: "clues 1,4,5 should be awarded"
            }
        },
        "neutral": {
            "student40": {
                2: "model ignores sorting instruction",
                3: "model ignores sorting instruction"
            },
            "student50": {
                1: "model ignores sorting instruction",
                2: "model ignores sorting instruction",
                3: "model ignores sorting instruction"
            }
        },
        "cycles":{
            "student40": {
                2: "model ignores sorting instruction",
                3: "model ignores sorting instruction"
            },
            "student50": {
                1: "model ignores sorting instruction",
                2: "model ignores sorting instruction",
                3: "model ignores sorting instruction"
            }
        },
        "breakout": {
            "student35": {
                3: "student missing same clue as loop, fails"
            },
            "student60": {
                5: "model ignores sorting instruction"
            },
            "student64": {
                6: "model starts paying attention to sorting instruction when word sort appears"
            },
            "student69": {
                2: "student fails"
            }
        }
    },
    "getSeason": {
        "start_node" : {
            "student14": {
                0: "model hallucinates month numbers instead of str"
            },
            "student45": {
                0: "model out of tokens"
            }
        },
        "fail": {
            "student31": {
                3: "model out of token"
            }
        },
        "neutral": {
            "student45": {
                1: "model out of token",
                2: "model out of token"
            },
            "student55": {
                3: "model run out of token"
            },
            "student9": {
                2: "model out of token",
                3: "model out of token"
            }
        },
        "success": {
            "student46": {
                3: "model guesses months correctly"
            },
            "student47": {
                1: "missing clue 1 implicit"
            },
            "student7": {
                3: "missing clue1 is implicit"
            }
        },
        "cycles": {
            "student31": {
                3: "model out of token"
            },
            "student55": {
                3: "model out of token"
            }
        },
        "breakout": {
            "student15": {
                4: "model out of token"
            },
            "student45": {
                3: "model out of token, thus less detail better"
            },
            "student6": {
                3: "model out of token"
            }
        }
    },
    "print_time": {
        "start_node": {
            "student57": {
                0: "model out of tokens"
            },
            "student77": {
                0: "first attempt correct"
            }
        },
        "success": {
            "student12": {
                3: "missing clue 1 is implicit"
            },
            "student36": {
                2: "missing clue 1 is implicit"
            },
            "student38": {
                1: "missing clue 1 is implicit"
            },
            "student42": {
                2: "missing clue 1 is implicit"
            },
            "student43": {
                1: "missing clue 1 is implicit"
            },
            "student54": {
                4: "missing clue 1 implicit"
            }
        },
        "fail": {
            "student57": {
                1: "model runs out of token"
            }
        },
        "neutral": {
            "student77": {
                1: "first attempt was correct"
            }
        }
    },
    "remove_odd": {
        "start_node": {
            "student0": {
                0: "model uses % which ignores floats"
            },
            "student41": {
                0: "model follows student instructions too closely, commits python error of modify list while iterating"
            }
        },
        "neutral": {
            "student0": {
                1: "same as prev attempt",
                2: "same as prev attempt",
                4: "same as prev attempt"
            },
            "student25": {
                1: "issue of using % ignores floats",
                2: "same as prev",
                3: "same as prev",
            },
            "student41": {
                1: "same as prev",
                2: "same as prev",
            }
        },
        "fail": {
            "student25": {
                4: "same as prev"
            },
            "student41": {
                3: "same as prev"
            }
        },
        "success": {
            "student18": {
                1: "missing clue 1,4 is implicit"
            }
        },
        "cycles": {
            "student0": {
                1: "same issue of % seen before",
                2: "same issue of % seen before"
            },
            "student25": {
                1: "same issue of %",
                2: "same as prev"
            },
            "student41": {
                3: "same python list out of index issue"
            }
        },
        "breakout": {
            "student0": {
                5: "issue of %, rephrasing helps"
            },
            "student17": {
                8: "student stuck between 2 cycles"
            },
            "student4": {
                6: "same errors as cycle"
            },
            "student51": {
                3: "same error as cycle"
            }
        }
    },
    "reverseWords": {
        "success": {
            "student1": {
                2: "5 return list implicit"
            },
            "student14": {
                3: "1,5 input+return implicit"
            },
            "student46": {
                1: "5 return is implicit"
            },
            "student7": {
                1: "1 implicit"
            }
        },
        "breakout": {
            "student1": {
                2: "argue this edge could be a2 not m2"
            },
        }
    },
    "set_chars": {
        "success": {
            "student19": {
                1: "missing clue 4 return string is implicit"
            },
            "student20": {
                3: "student should be awarded clue 1. 4 is implicit",
                4: "student should be awarded clue 1. 4 is implicit"
            },
            "student77": {
                1: "clue 4 implicit"
            }
        },
        "breakout": {
            "student20": {
                4: "this is loop over success state, ignore."
            }
        }
    },
    "sortBySuccessRate": {
        "fail": {
            "student33": {
                2: "student uses 'returning entries each on a separate line' which model interprets as print"
            },
            "student79": {
                4: "same issue as student33"
            }
        },
        "neutral": {
            "student79": {
                3: "model interprets put each element on separate line as print",
            }
        },
        "success": {
            "student64": {
                2: "clue 6 return is implicit"
            }
        },
        "breakout": {
            "student23": {
                2: "breakout edge leads to fail, student makes same mistake"
            },
            "student79": {
                4: "breakout edge leads into another cycle"
            }
        }
    },
    "sortedBooks": {
        "success": {
            "student29": {
                5: "missing clue 1 takes list of dict; implicit clue"
            }
        },
        "neutral": {
            "student49": {
                1: "Model ignores instruction to filter by author"
            }
        },
        "breakout": {
            "student67": {
                3: "student unsuccessful, keeps making same error--cycle could be cut short"
            }
        }
    },
    "times_with": {
        "start_node": {
            "student35": {
                0: "Model makes pyhton error: unhashable list because of meeting[1:] instead of meeting[1]. Model requires more info on nested list structure \
                I would argue this student does not get clue 2"
            },
            "student63": {
                0: "Model requires more info on nested list structure. Less ambiguous than student35, but still could be misinterpreted"
            }
        },
        "fail": {
            "student63": {
                1: "studenteval original is_success is wrong, this completion is successful"
            }
        },
        "success": {
            "student69": {
                1: "clue 1 return dictionary is implicit"
            },
            "student75": {
                5: "student hardcoded answer, somehow model got correct completion, even though prompt was wrong"
            }
        },
        "breakout": {
            "student50": {
                2: "Student goes on to make same mistake as loop"
            },
            "student59": {
                2: "I would argue this is an a4 not m4, structure of nested list"
            }
        }
    },
    "total_bill": {
        "success": {
            "student40": {
                2: "Missing clue 1. I think this student implicity included clue 1: 'input is a list'."
            },
            "student44": {
                1: "Missing clue 1,3,6,8. Very terse wording results in correct answer. I think this answer has low pass@k, can we verify it? Student got lucky."
            },
            "student60": {
                1: "Missing clue 3,4. This is because sales tax (clue 6) is umbrella term for clue 3,4"
            },
            "student64": {
                3: "missing clue 1,3,8. 1,3,8 could be implicit."
            }
        },
        "breakout": {
            "student64": {
                2: "breakout edge tagged as m4 but should be a4"
            }
        }
    },
    "pattern": {
        "start_node": {
            "student25": {
                0: "Model misinterprets student, produces increasing sequence of numbers in output. Possibly due to repetition of range(1, value+1)"
            },
            "student3": {
                0: "ambiguous wording, could be interpreted either way"
            }
        },
        "success": {
            "student17": {
                3: "Hardcoded ICL examples, thus model correct"
            },
            "student4": {
                1: "clue 5 return is implicit"
            },
            "student41": {
                3: "clue 1 input int is implicit"
            }
        },
        "neutral": {
            "student3": {
                2: "Ambiguous wording could be interpreted either way"
            }
        },
        "breakout": {
            "student41": {
                2: "I would say this edge is d4 not m4"
            }
        }
    },
    "readingIceCream": {
        "success": {
            "student27": {
                1: "Missing clue is 7, return total, which can be implicit."
            },
            "student32": {
                2: "Missing clue 1,5. I argue clue 5 should be awarded in attempt 1. \
                Clue 1, input is list of strings, is implicit."
            },
            "student62": {
                3: "Missing clue 1,4. 1 is implicit. 4 should have been awarded in attempt 2."
            },
            "student66": {
                2: "Missing clue 1,3. 1 is implicit. 3 should have been awarded? This is a python \
                    quirk where splitting on space is the same as splitting on \t. Student got somewhat lucky"
            }
        },
        "neutral": {
            "student70": {
                1: "Model thinks number == integer, rather than float. Student understood and corrected this."
            }
        },
        "cycles": {
            "student70": {
                1: "Model thinks number == integer, rather than float. Student understood and corrected this."
            }
        }
    },
    "planets_mass": {
        "success": {
            "student14": {
                4: "Student describes function incorrectly, missing many clues, but tests do not cover all cases, \
                    so student trivially succeeds."
            },
            "student53": {
                1: "Missing clue 1, which could be implicit? Interesting that model automatically associates value with dict"
            }
        },
        "neutral": {
            "student46": {
                1: "This student is an interesting example where by providing LESS words, model predicts correct. \
                    This is because originally, model is conflating instructions. Student breaks out of loop by removing \
                        instructions."
            },
            "student55": {
                1: "Capitalization missing",
                3: "I think this is still missing clue 2,3 which student removed"
            },
            "student65": {
                2: "Interesting case where planets the veriable and planets the concept is conflated by model.",
            }
        },
        "fail": {
            "student65": {
                3: "Interesting case where explicitly specifying input is dictionary makes model hallucinate planets_dict. \
                    possibly because of conflation with planets the word."
            }
        },
        "breakout": {
            "student46": {
                2: "This student is an interesting example where by providing LESS words, model predicts correct. \
                    This is because originally, model is conflating instructions. Student breaks out of loop by removing \
                        instructions."
            },
            "student14": {
                4: "Student rewrites to include capitalization, reaching success. However, Student describes function \
                    incorrectly, missing many clues, but tests do not cover all cases, so student trivially succeeds."
            },
            "student47": {
                3: "Cycle cut short, but student arguably would continue cycle."
            },
            "student55": {
                4: "May be tagging error, as recorded above. This edge actually adds clue 2,3 which student \
                    have previously removed, but deletion was not tagged"
            },
            "student65": {
                3: "Cycle cut short, but student arguably would continue cycle."
            }
        },
        "cycles":{
            "student55": {
                1: "Loop persists despite non-trivial edge because student is missing capitalization."
            },
            "student65": {
                2: "Interesting case where planets the veriable and planets the concept is conflated by model.",
            }
        },
        "start_node":{
            "student46": {
                0: "This student is an interesting example where by providing LESS words, model predicts correct. \
                    This is because originally, model is conflating instructions. Student breaks out of loop by removing \
                        instructions."
            },
        }
    },
    "fib": {
        "success": {
            "student11": {
                1: "Ignore because hardcoded numbers",
            },
            "student13": {
                10: "No need for clue 3 explanation of fib. It's a problem seen by models."
            },
            "student2": {
                3: "Hardcoded"
            },
            "student22": {
                2: "Hardcoded"
            },
            "student37": {
                1: "No need for clue 3 explanation of fib. It's a problem seen by models."
            }
        },
        "breakout": {
            "student2": {
                3: "Interesting case where model ignores wrong hardcoded instruction in favor of writing \
                a fib function (not is_fib as required). Only on 3rd attempt does model follow hardcoded"
            }
        }
    },
    "subtract_add": {
        "start_node": {
            "student68": {
                0: "Model misinterprets odd and even indexing. 0 indexing issue."
            }
        },
        "neutral": {
            "student29": {
                1: "Model ignored instruction of odd/even. 0 indexing issue"
            },
            "student66": {
                3: "Hardcoded"
            },
            "student68": {
                1: "Wrong base case of [], student did not consider.",
                2: "Model adds an additional store operation for first element, which is wrong"
            },
            "student70": {
                2: "Model out of tokens"
            }
        },
        "fail": {
            "student70": {
                4: "Clue 2 is worded ambiguously. Treat all elements as integers could mean list of integers."
            }
        },
        "cycles": {
            "student29": {
                1: "Model ignored instruction of odd/even. 0 indexing issue"
            },
            "student66": {
                3: "Hardcoded, student wrong."
            }
        }
    },
    "translate": {
        "success": {
            "student50": {
                1: "missing clues 3,6,7 are implicit"
            },
            "student59": {
                1: "missing clue 3,7 are implicit"
            },
            "student60": {
                3: "missing clue 3,7 are implicit"
            }
        }
    },
    "increaseScore": {
        "start_node": {
            "student33": {
                0: "Model uses if instead of elif, thus answer is wrong though prompt correct."
            }
        },
        "success": {
            "student23": {
                4: "sub clue 3 for clue 5. [1,2,3,4,6] and [1,3,4,5,6] both correct + \
                    student reaches success by attempt 1"
            },
            "student50": {
                1: "6 implicit. 4 missing, but tests pass because of coverage."
            },
            "student59": {
                1: "[1,3,4,5,6] ok"
            },
            "student60": {
                2: "[1,3,4,5,6] ok"
            },
            "student75": {
                1: "hardcoded"
            }
        }
    },
    "percentWin": {
        "fail": {
            "student10": {
                3: "model ignores clue 4"
            }
        },
        "success": {
            "student17": {
                5: "missing clue 6 is implied. Clue 1 is wrong, but thanks to python polymorphism passes"
            },
            "student18": {
                3: "same as student 17, string input instead of list input, but passes"
            },
            "student21": {
                2: "passes due to test coverage"
            },
            "student3": {
                2: "clue 6 return is implied"
            },
            "student30": {
                1: "clues 1,2,3 are included, though student gives step by step instructions."
            },
            "student4": {
                3: "clue 1 implied"
            },
            "student51": {
                3: "clue 1 implied"
            }
        },
        "neutral": {
            "student25": {
                2: "model rounds to 2 decimals instead of whole number"
            }
        },
        "cycles": {
            "student10": {
                3: "model ignores integer in prompt"
            }
        },
        "breakout": {
            "student26": {
                3: "next edge is breakout. Model ignores instruction to add %, until student specifies '%' (string)"
            },
            "student4": {
                3: "model ignores instruction to turn to integer, instead prefers next word of rounding"
            }
        }
    },
    # Arjun
    "laugh": {
        "neutral": {
            "student37": {
                1: "Student has all clues, but model still misinterpreting."
            }
        },
        "breakout": {
            "student8": {
                17: "Could argue that breakout edge is just loop cut short because student gives up"
            }
        }
    },
    "assessVowels": {
        "start_node": {
            "student13": {
                0: "model assumes lowercase"
            },
            "student37": {
                0: "model ignores case sensitive"
            },
            "student5": {
                0: "model ignores case sensitive"
            }
        },
        "neutral": {
            "student5": {
                1: "model ignores case sensitive instruction",
            }
        },
        "fail":{
            "student5": {
                2: "model ignores case sensitive instruction"
            }
        },
        "cycles": {
            "student5": {
                1: "model ignores case sensitive instruction",
                2: "model ignores case sensitive instruction"
            }
        }
    },
    "altText": {
        "success": {
            "student75": {
                2: "Student is trivially correct because test cases not exhaustive."
            }
        },
        "neutral": {
            "student23": {
                3: "Interesting case where student has all clues, but model misinterprets student in \
                    'technically' correct way, but a way a human would never do--order of output.",
                4: "same as previous attempt",
                5: "same as previous attempt"
            },
            "student35": {
                1: "Same model misinterpretation issue as 23. Model does not consider order of output."
            },
            "student40": {
                1: "Model runs out of tokens but would be correct.",
                2: "same as previous attempt",
                3: "same as previous attempt",
                4: "same as previous attempt"
            },
            "student63": {
                1: "hallucination",
            }
        },
        "fail": {
            "student60": {
                2: "Model includes space in alternating letters"
            },
            "student63": {
                2: "Same model misinterpretation as 23."
            }
        },
        "start_node": {
            "student35": {
                0: "Same model misinterpretation issue as 23."
            },
            "student40": {
                0: "Model runs out of tokens"
            },
            "student63": {
                0: "Same misinterpretation as 23."
            }
            
        },
        "cycles": {
            "student23": {
                3: "Interesting case where student has all clues, but model misinterprets student in \
                    'technically' correct way, but a way a human would never do--order of output. Thus, keeps cycling.",
            },
            "student35": {
                1: "Same model misinterpretation issue as 23."
            },
            "student40": {
                3: "Model runs out of tokens error."
            }
        },
        "breakout": {
            "student23": {
                4: "Same model order misinterpretation issue"
            },
            "student40": {
                5: "Breaksout because model manages to fit within token limit"
            }
        }
    },
    "changeSection": {
        "start_node": {
            "student10": {
              0: "model misinterprets instruction, backwards as reverse over of splits, not reverse letters"
            },
            "student21": {
                0: "same as student10; language ambiguity- 'concatenated' means append to end, model confised"
            },
            "student26": {
                0: "1-index instead of 0-index"
            },
            "student30": {
                0: "Model misinterprets before as after"
            }
        },
        "success": {
            "student25": {
                1: "Interesting case where model manages to successfully interpret ambiguous language of student."
            }
        },
        "fail": {
            "student18":{
                3: "Model does wrong recursion order",
            },
            "student21": {
                5: "same error as previous attempt",
            },
            "student30": {
                4: "same as previous attempt"
            }
        },
        "neutral":{
            "student26": {
                1: "display instead of return makes model misinterpret print instead of return"
            },
            "student21": {
                1: "same error as previous attempt",
                2: "same error as previous attempt",
                3: "same error as previous attempt",
                4: "same error as previous attempt",
            },
            "student30": {
                # note student 30 has a success at attempt 1, not recorded correctly
                2: "model misinterpretation same as student10",
                3: "model misinterprets order",
            }
        },
        "cycles": {
            "student30": {
                3: "model misinterpretation, same as previous",
            }
        },
        "breakout": {
            "student21": {
                2: "breakout goes into another cycle"
            }
        }
    }
    
}

IGNORE_SUCCESS = {
    # student is trivially successful due to lacking test coverage
    "planet_mass" : ["student14"],
    "altText": ["student75"],
    "fib": ["student11", "student2","student22"],
    "increaseScore": ["student75"],
    "percentWin": ["student21"],
    "sort_physicists": ["student77","student12","student57"]
}


PROBLEM_TO_NUM_STUDENTS_FULL = {
    "add_int": 10,
    "add_up": 17,
    "add_word": 14,
    "altText": 15,
    "andCount": 12,
    "assessVowels": 12,
    "changeSection": 13,
    "check_for_aspen": 12,
    "check_prime": 12,
    "combine": 10,
    "convert": 14,
    "correctNumberofPlayers": 12,
    "create_list": 10,
    "edit_col": 12,
    "exp": 15,
    "fib": 10,
    "findHorizontals": 12,
    "find_multiples": 12,
    "generateCardDeck": 15,
    "getSeason": 17,
    "hasHorizontalWin": 15,
    "has_qu": 10,
    "increaseScore": 15,
    "laugh": 11,
    "layoverTrips": 7,
    "meeps_morps": 12,
    "mod_end": 10,
    "multisplit": 17,
    "order_strings": 8,
    "partialWordle": 11,
    "pattern": 14,
    "percentWin": 14,
    "planets_mass": 16,
    "print_time": 10,
    "readingIceCream": 11,
    "reduce": 14,
    "remove_odd": 14,
    "reverseWords": 14,
    "set_chars": 10,
    "sortBySuccessRate": 15,
    "sort_physicists": 10,
    "sortedBooks": 12,
    "student_grades": 12,
    "subtract_add": 11,
    "times_with": 15,
    "topScores": 16,
    "total_bill": 15,
    "translate": 15
}

# NOT COUNTING STUDENTS WITH 1 ATTEMPT
PROBLEM_TO_NUM_STUDENTS_STRICT = {
   "topScores": 11,
   "translate": 7,
   "sortBySuccessRate": 13,
   "convert": 12,
   "planets_mass": 9,
   "times_with": 11,
   "increaseScore": 8,
   "reduce": 2,
   "subtract_add": 9,
   "check_for_aspen": 4,
   "add_word": 9,
   "sortedBooks": 10,
   "create_list": 6,
   "combine": 5,
   "hasHorizontalWin": 6,
   "total_bill": 13,
   "layoverTrips": 4,
   "has_qu": 3,
   "order_strings": 3,
   "remove_odd": 13,
   "changeSection": 11,
   "getSeason": 15,
   "pattern": 6,
   "student_grades": 6,
   "generateCardDeck": 13,
   "fib": 8,
   "print_time": 8,
   "correctNumberofPlayers": 3,
   "exp": 2,
   "percentWin": 12,
   "meeps_morps": 4,
   "sort_physicists": 9,
   "assessVowels": 8,
   "add_int": 6,
   "readingIceCream": 11,
   "laugh": 9,
   "andCount": 1,
   "partialWordle": 2,
   "set_chars": 8,
   "mod_end": 4,
   "add_up": 15,
   "findHorizontals": 8,
   "multisplit": 3,
   "altText": 8,
   "reverseWords": 9,
   "check_prime": 8,
   "find_multiples": 9,
   "edit_col": 2
}

if __name__ == "__main__":
    """
    for each problem check that the student exceptions
    are indeed exceptions, i.e not majority
    """
    PROBLEM_TO_NUM_STUDENTS = PROBLEM_TO_NUM_STUDENTS_FULL
    THRESHOLD = 0.4
    failing_problems = []
    for prob in SUCCESS_CLUES.keys():
        if prob not in KNOWN_EXCEPTIONS.keys():
            continue
        exceptions = KNOWN_EXCEPTIONS[prob]
        student_exceptions = set()
        for _, v in exceptions.items():
            student_exceptions.update(set(list(v.keys())))
        if len(student_exceptions) > (THRESHOLD * PROBLEM_TO_NUM_STUDENTS[prob]):
            failing_problems.append((prob, len(student_exceptions), PROBLEM_TO_NUM_STUDENTS[prob]))
    
    EXCEPTIONS = [
        "readingIceCream" # some of these exceptions are tagging errors
    ]
    failing_problems = [f for f in failing_problems if not f[0] in EXCEPTIONS]
    message = f"failing problems {failing_problems}, THRESHOLD: {THRESHOLD}"
    assert len(failing_problems) == 0, message
    print(message)