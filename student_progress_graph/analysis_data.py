SUCCESS_CLUES = {
    "add_up": [1,2,3,4,5],
    "add_int": [1,2,3,4],
    "topScores": [1,2,3,4,5,6]
}
KNOWN_EXCEPTIONS = {
    "add_int": {
        # false success, does not have all clues but is success
        "success": {
            # username: {attempt_id: exception reason}
            "student19": {"1": "clue 1 optional, but more efficient"},
            "student36": {"1": "clue 1 optional, but more efficient"},
            "student54": {"4": "clue 1 optional, but more efficient - student has long path to success"}
        },
        # false neutral, should be success because has all clues
        "neutral": {
            "student38": {"1": "marked as neutral because not last attempt, but successful",
                            "2": "this attempt follows a previous success"},
        },
        # false fail, should be success because all clues
        "fail": {
            "student38": {"3": "this final attempt follows a previous success"},
        }
    },
    "add_up": {
        "success": {
            "student24": {"1": """incomplete clues is successful due to use of python try-except
                          (student mentions 'error' in prompt)"""}
        },
        "neutral": {
            "student65": {"1": "has all clues, but still fails because model interprets 'number' as int",
                          "2": "same as previous attempt",
                          "3": "same as previous attempt",
                          "4": "same as previous attempt"}
        },
        "fail":{
            "student65": {"5": "has all clues, but still fails because model interprets 'number' as int"}
        }
    },
    "topScores": {
        "success": {},
        "neutral": {
            "student45": {"1":"student with all clues gets fail because of LLM runs out of tokens",
                          "2":"same as previous attempt",
                          "3":"same as previous attempt",
                          "4":"same as previous attempt",
                          "5":"same as previous attempt",
                          "6":"same as previous attempt"},
            "student53": {"4": """student has all clues; wording leads to LLM fail. Good example to highlight,
                          since student eventually gets it right. What did they change? Got rid of 'lookback'
                          statements""",
                          "6": "same as previous attempt",
                          "7": "same as previous attempt",
                          "8": "same as previous attempt",
                          "9": "same as previous attempt"
                          }
        },
        "fail": {
            "student45": {"7":"student with all clues gets fail because of LLM runs out of tokens"}
        }
    }
}