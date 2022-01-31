import requests as r
import json

def get(url: str) -> dict:
    return r.get(url).json()