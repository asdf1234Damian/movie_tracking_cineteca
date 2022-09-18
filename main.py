import requests
import requests_random_user_agent
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd 
from thefuzz import fuzz

#Global variables
curr_session = requests.session() 
tomorrow =( datetime.today()+timedelta(days=1)).strftime("%Y-%m-%d")

def get_movies()->dict:
    movies = []
    req = curr_session.get(f"https://www.cinetecanacional.net/controlador.php?opcion=carteleraDia&dia={tomorrow}" )
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, "html.parser")
        for mov_c in soup.findAll("div",id="contenedorPelicula"):
            metadata = mov_c.find("p",class_="peliculaMiniFicha").text[1:-1]
            movies.append({
                "name_spanish":mov_c.find("p",class_="peliculaTitulo").text,
                "original_name":metadata.split(",")[0],
                "director":metadata.split(",")[1][7:],
                "country":metadata.split(",")[2],
                "year":metadata.split(",")[3],
                "duration":metadata.split(",")[4][6:][:-1],
                })
        return movies
    else:
        print(f"[{datetime.now()}] Error req/res [Cineteca]")
        return {"error":req.status_code}


def get_letterbox_url(title:str,director:str)->str|None:
    letterbox_res = curr_session.get(f"https://letterboxd.com/search/films/{title}")
    soup = BeautifulSoup(letterbox_res.text, "html.parser")
    results = soup.find("ul",class_="results")
    if not (results is None):
        for li in results.findAll("li"):
            card = li.find("div",class_="film-detail-content")
            meta = card.find("p",class_="film-metadata")
            if not (meta is None):
                for a in meta.findAll("a"):
                    if fuzz.ratio(a.text, director) > 75:
                        return card.find("a")["href"]
    return None


def get_lttrbox_rating(url:str)->str|None:
    try :
        letterbox_res = curr_session.get(f"https://letterboxd.com{url}")
        soup = BeautifulSoup(letterbox_res.text, "html.parser")
        metadata =  soup.find("script",type="application/ld+json").text
        rating = json.loads( metadata.split("*/")[1].split("/*")[0].strip())["aggregateRating"]["ratingValue"]
        return rating
    except:
        return None

def main()->None:
    df = pd.DataFrame()
    movies = get_movies()
    for mov in movies[:]:
        lttrbox_url = get_letterbox_url(mov['original_name'],mov['director'])
        if lttrbox_url is None:
            pass
        else:
            mov["rating"] = get_lttrbox_rating(lttrbox_url) 
        movie_record = pd.DataFrame(data=mov,index=[0])
        df = pd.concat([df,movie_record],axis=0,ignore_index=True)
        sleep(1)
    df.sort_values("rating",ascending=False).to_csv(f"./data/{tomorrow}.csv",index=False)

if __name__ == "__main__":
    main()
