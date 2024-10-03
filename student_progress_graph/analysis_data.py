"""
[X] add_up
[X] add_int
[X] topScores
- total_bill
- laugh
- translate
- planets_mass
- altText
- add_word
- assessVowels
- changeSection
"""

SUCCESS_CLUES = {
    "add_up": [1,2,3,4,5],
    "add_int": [1,2,3,4],
    "topScores": [1,2,3,4,5,6],
    "total_bill": [1,2,3,4,5,6,7,8],
    "laugh": [1,2,3,4,5,6],
    # "translate": [1,2,3,4,5,6,7],
    "planets_mass": [1,2,3,4,5,6],
    # "altText": [1,2],
    # "readingIceCream": [1,2,3,4,5,6,7]
    
}
KNOWN_EXCEPTIONS = {
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
        "neutral": {
            "student65": {1: "has all clues, but still fails because model interprets 'number' as int",
                          2: "same as previous attempt",
                          3: "same as previous attempt",
                          4: "same as previous attempt"}
        },
        "fail":{
            "student65": {5: "has all clues, but still fails because model interprets 'number' as int"}
        },
        "cycles": {
            "student65": {
                2: "not an issue, since first edge in loop"
            }
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
    }
    
}

IGNORE_SUCCESS = {
    "planets_mass": [
        "student14", # student is trivially successful due to lacking test coverage
    ]
}


PROBLEM_TO_NUM_STUDENTS = {
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

if __name__ == "__main__":
    """
    for each problem check that the student exceptions
    are indeed exceptions, i.e not majority
    """
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
            failing_problems.append((prob, PROBLEM_TO_NUM_STUDENTS[prob]))
    
    message = f"failing problems {failing_problems}, THRESHOLD: {THRESHOLD}"
    assert len(failing_problems) == 0, message
    print(message)