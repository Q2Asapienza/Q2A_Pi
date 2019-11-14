#!/usr/bin/python3
from q2a import Q2A,Question,Like
import json

#globals
loginData = json.load(open('./data/login.json', 'r'))
USERNAME = loginData["username"]
PASSWORD = loginData["password"]

if __name__ == "__main__":
    separator = lambda: print("===============")
    
    #creating interface
    q2a = Q2A(USERNAME,PASSWORD)

    #loading session from disk
    print("SESSION FILE... ",end="")
    if(not q2a.sessionLoad()):
        #couldn't load, creating new session
        print("NOT OK\nLOGIN... ",end="")
        q2a.sessionCreate()
        q2a.sessionSave()
    print("OK")
    
    separator()

    #getting questions
    print("GETTING QUESTIONS...")
    questions = q2a.getQuestions()
    print("GOT: " + str(len(questions)) + " questions")
    separator()

    print("LAST EDITS...")
    for question in questions:
        print(question.title, question.lastEdit)
    separator()
    
    print("DONE!")  
