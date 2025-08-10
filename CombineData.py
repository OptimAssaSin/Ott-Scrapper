from OttScrapper.releases.scrappers.OttPlayScraper import scrape_ott_play
from OttScrapper.releases.scrappers.LiveMintScrapper import scrape_livemint_urls
from thefuzz import process
import spacy
import dateparser
from spacy.matcher import PhraseMatcher



canon_forms=[
    "Amazon Prime video", "Netflix", "Disney+ Hotstar", "Sony Liv", "Zee5", "Apple TV","Lionsgate Play", 
]

platform_patters={
    "Amazon Prime Video": ["amazon prime video", "prime video", "amazon prime", "prime"],
    "Netflix": ["netflix"],
    "Disney+ Hotstar": ["disney+ hotstar", "hotstar", "jiohotstar"],
    "SonyLIV": ["sonyliv", "sony liv"],
    "Apple TV+": ["apple tv+"],
    "JioCinema": ["jiocinema"],
    "ZEE5": ["zee5"],
    "Lionsgate Play": ["lionsgate play"]
}

known_languages = [
    "Hindi", "English", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali"
]
# Create a lowercase version for efficient, case-insensitive checking
known_languages_lower = {lang.lower() for lang in known_languages}

nlp = spacy.load("en_core_web_sm")
matcher=PhraseMatcher(nlp.vocab, attr="LOWER")

for platform, patterns in platform_patters.items():
    patterns=[nlp(text) for text in patterns]
    matcher.add(platform, None, *patterns)

def normalize_platform_name(name):
    if not name:
        return None
    
    correctedName, score= process.extractOne(name, canon_forms)
    if score < 70:
        correctedName = name
    
    doc=nlp(correctedName.lower())
    matches=matcher(doc)
    if matches:
        matchID, _, _= matches[0]
        return nlp.vocab.strings[matchID]
    return correctedName

def date_Parser(date):

    if not date:
        return None
    try:
        parseDate=dateparser.parse(date, settings={"TO_TIMEZONE": "UTC"}) 
        if parseDate:
            return parseDate.strftime("%d-%m-%Y")
        return None
    except Exception as e:
        return None
    
def cleanData(data):

    cleanedData={}

    for item in data:
        name=item.get("name")
        ott=item.get("ott") or item.get("platform")
        date=item.get("date") or item.get("release_date")
        languages= item.get("languages") or item.get("language")

        if not name or not ott or not date or not languages:
            continue

        cleanedLang=None 

        if isinstance(languages, list):
            filtered=[lang for lang in languages if lang.lower() in known_languages_lower]
            if filtered:
                cleanedLang=filtered

        

        normalizedOtt= normalize_platform_name(ott)

        if normalizedOtt not in canon_forms:
            continue #to keep only known platforms

        formattedDate=date_Parser(date)

        uniqueKey=(name.lower().strip(), normalizedOtt)

        if uniqueKey not in cleanedData:
            cleanedData[uniqueKey]={
                "name": name.strip(),
                "ott": normalizedOtt,
                "date": formattedDate,
                "languages": languages
            }
    return list(cleanedData.values())



if __name__=="__main__":
    data_1= scrape_ott_play()
    print(data_1)
    data_2= scrape_livemint_urls()

    data= data_1 + data_2
    
    scrapped_data= cleanData(data)
    for item in scrapped_data:
        print(item)