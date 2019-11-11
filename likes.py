#!/usr/bin/python3
from Q2AInterface import Q2AInterface
import pickle
import json

#globals
loginData = json.load(open('./data/login.json', 'r'))
USERNAME = loginData["username"]
PASSWORD = loginData["password"]

if __name__ == "__main__":
    separator = lambda: print("===============")

    #creating interface
    q2a = Q2AInterface(USERNAME,PASSWORD)
    
    #loading session from disk
    print("SESSION FILE... ",end="")
    if(not q2a.loadSession()):
        #couldn't load, creating new session
        print("NOT OK\nLOGIN... ",end="")
        q2a.createSession()
        q2a.saveSession()
    print("OK")
    
    separator()
    
    #getting pages
    print("GETTING PAGES...")
    pages = q2a.get_pages()
    print("GOT: " + str(len(pages)) + " pages")
    separator()

    #getting questions
    print("GETTING QUESTIONS...")
    questions = set()
    for page in pages:
        q2a.get_threads(page,questions)
    print("GOT: " + str(len(questions)) + " questions")
    separator()

    #getting likes    
    likes = []
    lastLikesCount = 0
    noLikesThread = []

    print("GETTING LIKES...")
    count = 0
    for question in questions:
        q2a.get_likes(question,likes)
    print("GOT: "+str(len(likes))+" likes")
    separator()

    #sending likes
    print("SENDING LIKES:")
    delete = []
    for i in range(len(likes)):
        result = q2a.sendLike(likes[i])
        if(result == None):
            delete.append(i)
        else:
            print("NOT ALL LIKES SENT!!!")
            print(result)
            break
    print("LIKES SENT: " + str(len(delete)))
    separator()
    
    print("DONE!")  
