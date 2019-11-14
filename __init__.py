import pickle
import requests
import cssselect

from lxml import html
from typing import List

class Q2A:
    BASE_URL = "https://q2a.di.uniroma1.it/"
    QUESTION_PAGE = "https://q2a.di.uniroma1.it/questions/"
    LOGIN_URL = "https://q2a.di.uniroma1.it/login?to="
    USER_URL = "https://q2a.di.uniroma1.it/user"

    def __init__(self, username:str, password:str, category = "fondamenti-di-programmazione-19-20"):
        """
        """
        self.username = username
        self.password = password
        self.category = category

        self.session = requests.session()
        self.session.headers.update({"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36"})

    #region utility
    def getHTMLFromURL(self, url:str, session) -> html.HtmlElement:
        return html.fromstring(session.get(url).text)

    def getCode(self, tree:html.HtmlElement) -> str:
        return tree.cssselect('input[name="code"]')[0].attrib['value']
    #endregion

    #region SESSION management
    def sessionCreate(self):
        """Create a new requests session for comunicating with Q2A.
        Creating a session is necessary for acting as a logged in user
        WARNING: SAVING CURRENT SESSION TO A FILE IS INSECURE AND AKIN TO SAVING PASSWORD TO A TEXT FILE, BE CAREFUL!

        Params:
        filename(str): the path of the file in wich the session will be written

        Return:
        True if the session was loaded and still valid, False otherwise
        """

        # Get csrf token
        page = self.session.get(Q2A.BASE_URL).text
        tree = html.fromstring(page)
        self

        loginPOSTBody = {
            "emailhandle": self.username, 
            "password": self.password,
            "remember": '1',
            "code": self.getCode(tree),
            "dologin": "Login",
        }

        # Perform login
        self.session.post(Q2A.LOGIN_URL, data = loginPOSTBody)

        if(not self.logged_in()):
            raise Exception("CAN'T LOGIN")

    #region sessionfile
    def sessionLoad(self, filename = "./data/q2a.ses") -> bool:
        """
        Save current session to a file.
        WARNING: SAVING CURRENT SESSION TO A FILE IS INSECURE AND AKIN TO SAVING PASSWORD TO A TEXT FILE, BE CAREFUL!

        Params:
        filename(str): the path of the file in wich the session will be written

        Return:
        True if the session was loaded and still valid, False otherwise
        """
        try:
            #try to load the last session
            with open(filename,'rb') as sess_file:
                self.session = pickle.load(sess_file)
        except Exception:
            return False

        return self.logged_in()

    def sessionSave(self, filename = "./data/q2a.ses"):
        """
        Save current session to a file.
        WARNING: SAVING CURRENT SESSION TO A FILE IS INSECURE AND AKIN TO SAVING PASSWORD TO A TEXT FILE, BE CAREFUL!

        Params:
        filename(str): the path of the file in wich the session will be written
        """
        with open(filename, 'wb') as sess_file:
            pickle.dump(self.session, sess_file)
    #endregion

    #endregion

    #region PROFILE INFO
    def logged_in(self):
        return self.username in self.session.get(self.USER_URL).url

    def profileInfo(self):
        pass
    #endregion

    #region Utility for user
    def getAllQuestions(self, category:str = None) -> list:
        page = 1
        questions = []
        while(True):
            added = self.getQuestions(category=category,page=page)
            #going to next page
            if(len(added) == 0):
                break
            questions.extend(added)
            page += 1
        return questions

    def getQuestions(self, page:int = 1, category:str = None) -> list:
        """
        Get questions from a page.

        Params:
        page(int): The number of the page
        category(str): The id of the category

        Return:
        A list containing the Questions found
        """
        if(category == None):
            category = self.category

        questions = []
        #loading page
        tree = self.getHTMLFromURL(self.QUESTION_PAGE+category +"?start=" +str((page-1)*20),self.session)
        currentQuestions = tree.cssselect('div.qa-q-list-item')
        for question in currentQuestions:
            question_id = question.attrib['id'][1:]
            question_title = question.cssselect(".qa-q-item-title span")[0].text
            who = question.cssselect('.qa-user-link')[0].attrib["href"]
            lastEdit = {
                "what":question.cssselect('.qa-q-item-what')[0].text,
                "when":question.cssselect('.qa-q-item-when-data')[0].text,
                'who':User(who[who.rfind('/')])
                }
            if(question_id not in questions):
                questions.append(Question(question_id,self,title=question_title, lastEdit=lastEdit))
        return questions

    def getLikes(self, questions:list ,refresh:bool=False) -> list:
        likes = []
        question:Question
        for question in questions:
            if(refresh):
                question.get()
                likes.extend(question.likes)
        return likes
    #endregion

class Like:
    LIKE_HEADERS = {
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://q2a.di.uniroma1.it",
    }

    def __init__ (self, id:str, question, voted:bool):
        self.id = id
        self.question:Question = question
        self.headers = Like.LIKE_HEADERS.copy()
        self.question = question
        self.headers['referer'] = self.question.id
        self.voted = voted

    def vote(self, upVote:bool = True):
        #navigate to Question otherwise site goes MAD (and meanwhile i update code)
        tree = self.question.getHTML()
        form = tree.xpath("//div[@id='voting_"+self.id+"']/ancestor::form")[0]

        postData = {
            "postid": self.id,
            "vote": int(upVote),
            "code": self.question.q2a.getCode(form),
            "qa": "ajax",
            "qa_operation": "vote",
            "qa_root": "./",
            "qa_request": self.question.id,
        }

        result = self.question.q2a.session.post(Like.LIKE_HEADERS["origin"], headers=self.headers, data = postData).text.split('\n')
        if result[1] == '1':
            return True
        
        return result[2]

class Question:
    __dict = {}
    __id:str

    @property
    def id(self) -> str:
        return self.__id
    likes:list
    lastEdit:dict
    title:str
    preview:str

    def __init__(self,id,q2a,**args):
            self.q2a:Q2A = q2a
            for key,value in args.items():
                self.__setattr__(key,value)

            if id in Question.__dict:
                self = Question.__dict[id]
            else:
                self.__id = id
                #self.update()#TODO: ABILITA
                Question.__dict[id] = self
    
    def getHTML(self):
        return self.q2a.getHTMLFromURL(Q2A.BASE_URL+self.__id, self.q2a.session)

    def get(self):
        self.likes = []
        tree = self.q2a.getHTMLFromURL(Q2A.BASE_URL+self.__id, self.q2a.session)
        for like in tree.cssselect(".qa-voting"):
            name = like.cssselect(".qa-vote-one-button")[0].get("name")
            voted = name if name == None else (name.split("_")[2] == '0')
            self.likes.append(Like(like.attrib["id"].split("_")[1],self, voted))
        return self.likes
    
    #region compare utility
    def __hash__(self):
        return id

    def __eq__(self, other):
        if isinstance(other, Question):
            return self.id == other.id
        elif isinstance(other,int):
            return self.id == other
    
    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result 
    #endregion

class User:
    __id:str
    @property
    def id(self):
        return self.__id
    
    def __init__(self,id):
        self.__id = id
