import re
import certifi
import requests
import ssl
import urllib.request
import time
from bs4 import BeautifulSoup
from bs4 import SoupStrainer


def main():
  print(f"This program started at : {time.asctime()}")
  URL = "https://en.wikipedia.org/wiki/List_of_fighting_games"
  page = requests.get(URL)

  ## 
  # This function is the search parameters when parsing through the retrived href links.
  # It will filter any anchor tags that are missing the title and href attributres, as well as filtering
  # any pages that redirect to a 404 page, different "lists" pages, specific sections of an existing link,
  # pages regarding wikipedia, or outside URLs. We are also separating links that redirect to franchises of individual
  # games (Removing Street Fighter (series) from the list of Street Fighter games). The (series) tag will be parsed to 
  # a different list
  ##
  def gameParams(tag):
    return tag.has_attr("title") and tag.has_attr("href") and\
      not re.compile("/w/index.php|List_|#|^http|help|Special:[A-Za-z]|_\(series\)").search(tag["href"]) and\
      not re.compile("wikipedia",re.IGNORECASE).search(tag["title"])
  ## 
  # This function runs similarly to gameParams, with the only difference being parsing exclusively for series tags.
  ##
  def seriesParam(tag):
    return tag.has_attr("title") and tag.has_attr("href") and re.compile("_\(series\)").search(tag["href"])\
      and not re.compile("#").search(tag["href"])

  # This strainer will have Beautiful soup only parse for anchor tags.
  onlyLinks = SoupStrainer("a")
  soup = BeautifulSoup(page.content, "html.parser", parse_only=onlyLinks)
  # Searching for links that match the defined parameters and stripping the data of duplicate links
  hrefList = soup.find_all(gameParams)
  hrefSet = set(hrefList)

  ##
  # Searching for links that redirect to franchises and attempt to strip the date of duplicate links.
  # Due to discrepencies in how some series are labeled, some duplicates will manage to remain.
  ##
  seriesList = soup.find_all(seriesParam)
  hrefSet = set(seriesList)
  seriesList = list(hrefSet)

  ##
  # For every entry in hrefList, a URL link will be created for each available game and check if each page as an html
  # tag with the class "infobox-image". If the page does have the tag, the anchor tag containing the image URL will be
  # extracted and parsed to extract the actual image.
  ##
  for game in hrefList:
    URL = f"https://en.wikipedia.org{game['href']}" #Creating the desired URL used to retrieve the page.
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    wikiLink = soup.find(class_="infobox-image") #Extracting the infobox that contains the cover art of the game.
    ##
    # This will check if the wikiLink exists. If it does, The image URL will always be in the first entry in the tag's
    # content list, retrievable by specifying the href tag. Then a new URL link is created to request for the page
    # containing the URL that contains the saveable URL, which will then be saved.
    # Otherwise it will pass.
    ##
    if wikiLink is not None:
      URL = f"https://en.wikipedia.org{(wikiLink.contents[0]['href'])}"
      page = requests.get(URL)
      soup = BeautifulSoup(page.content, "html.parser")
      imgURL = soup.find(id="file")
      if imgURL is not None:
        URL = f"https:{imgURL.contents[0]['href']}" # The full, completed, URL.
        context = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
        req.addheaders = [('User-agent', 'FightingGameCoversBot/1.0')]
        res = req.open(URL, timeout=10)

        filename = game['title']
        # This is for edge cases where "/" or ":" is present in the title.
        filename = filename.replace("/", "_")
        filename = filename.replace(":", " -")
        # Acquiring the image's file extension
        fileType = re.compile(".[a-z]+$",re.IGNORECASE).search(URL)
        # Creating the save path
        saveTo = f"./covers/{filename}{fileType.group()}"
        with open(saveTo, "wb") as f:
          f.write(res.read())
    time.sleep(1)
  print("All covers have been downloaded.")
  print(f"Program finished at {time.asctime()}")
  return

if __name__ == "__main__":
  main()