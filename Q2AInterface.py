import pickle
import requests
from lxml import html

class Q2AInterface():
    __BASE_URL = "https://q2a.di.uniroma1.it/"
    __QUESTION_PAGE = "https://q2a.di.uniroma1.it/questions/fondamenti-di-programmazione-19-20?start="
    __LOGIN_URL = "https://q2a.di.uniroma1.it/login?to="
    __USER_URL = "https://q2a.di.uniroma1.it/user"

    __like_post_headers = {
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://q2a.di.uniroma1.it",
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        
    def loadSession(self, filename = "./data/q2a.ses"):
        try:
            #try to load the last session
            with open(filename,'rb') as sess_file:
                self.session = pickle.load(sess_file)
        except Exception as ex:
            return False
        
        return self.logged_in()

    def saveSession(self, filename = "./data/q2a.ses"):
        with open(filename, 'wb') as sess_file:
            pickle.dump(self.session, sess_file)

    def createSession(self):
        self.session = requests.session()
        self.session.headers.update({"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36"})

        # Get csrf token
        page = self.session.get(self.__BASE_URL).text
        tree = html.fromstring(page)
        self.__getQ2ACode(tree)

        loginPOSTBody = {
            "emailhandle": self.username, 
            "password": self.password,
            "remember": '1',
            "code": self.__code,
            "dologin": "Login",
        }

        # Perform login
        self.session.post(self.__LOGIN_URL, data = loginPOSTBody)

        if(not self.logged_in()):
            raise Exception("CAN'T LOGIN")

    def __getQ2ACode(self, tree):
        self.__code = tree.cssselect('input[name="code"]')[0].attrib['value']
    
    def get_threads(self, url, threads = set()):
        tree = html.fromstring(self.session.get(url).text)
        for question in tree.cssselect('div.qa-q-list-item'):
            qid = question.attrib['id'][1:]
            threads.add(qid)
        return threads
    
    def logged_in(self):
        return self.username in self.session.get(self.__USER_URL).url
    
    def get_pages(self):
        current = 0
        pages = []
        while(True):
            result = self.session.get(self.__QUESTION_PAGE+str(current))
            tree = html.fromstring(result.text)

            if(len(tree.cssselect('.qa-page-selected')) == 0):
                break
            
            pages.append(result.url)
            current += 20
        return pages
    
    def get_likes(self, thread, likes = []):
        result = self.session.get(self.__BASE_URL+str(thread))
        tree = html.fromstring(result.text)
        for form in tree.cssselect('form'):
            like = form.cssselect('.qa-vote-up-button')
            if (len(like)>0):
                code = form.cssselect('input[name="code"]')[0].attrib['value']
                likes.append((like[0].attrib['name'],thread,code))
        return likes

    def sendLike(self,like):
        #navigate to thread otherwise site goes MAD (and meanwhile i update code)
        self.__getQ2ACode(html.fromstring(self.session.get(self.__BASE_URL+like[1]).text))

        command, likeID, vote, alikeID = like[0].split("_")
        postData = {
            "postid":likeID,
            "vote":vote,
            "code": like[2],
            "qa":"ajax",
            "qa_operation":command,
            "qa_root":"./",
            "qa_request":like[1],
        }
        self.session.headers.update({'referer': self.__BASE_URL+like[1]})

        result = self.session.post(self.__BASE_URL, headers=self.__like_post_headers, data = postData).text.split('\n')
        if result[1] == '1':
            return None
        
        return result[2]
