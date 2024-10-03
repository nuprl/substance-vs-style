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
    "translate": [1,2,3,4,5,6,7],
    "planets_mass": [1,2,3,4,5,6],
    "altText": [1,2]
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