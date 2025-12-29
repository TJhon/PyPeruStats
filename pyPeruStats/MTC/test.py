from duckduckgo_search import DDGS as search
from rich import print


all = search().text("TRFM54713", max_results=20, region="ue-es")
print(all)
