import re
import requests
from urllib.parse import quote

API_URL = "https://text.pollinations.ai/"

def call_ai(prompt, model):
    encoded_prompt = quote(prompt, safe="")
    response = requests.get(API_URL + encoded_prompt, params={"model": model}, headers={"User-Agent": "GMC-Smart-Negotiation/1.0"}, timeout=90)
    response.raise_for_status()
    result = response.text.strip()
    if not result:
        raise ValueError("وصل رد فارغ من خدمة الذكاء الاصطناعي.")
    return result

def extract_offer(text):
    for pattern in [r"OFFER\s*:\s*([0-9,]+)", r"PRICE\s*:\s*([0-9,]+)", r"السعر\s*:\s*([0-9,]+)", r"العرض\s*:\s*([0-9,]+)"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None

def extract_message(text):
    match = re.search(r"MESSAGE\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    if match:
        result = match.group(1).strip()
        result = re.sub(r"\n*DECISION\s*:.*$", "", result, flags=re.I | re.S)
        return result.strip()
    cleaned = re.sub(r"(OFFER|PRICE|السعر|العرض)\s*:\s*[0-9,]+", "", text, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_decision(text):
    match = re.search(r"DECISION\s*:\s*(ACCEPT|REJECT|COUNTER)", text, re.IGNORECASE)
    return match.group(1).upper() if match else "UNKNOWN"

def agent_response(prompt, model, fallback_offer):
    raw = call_ai(prompt, model)
    offer = extract_offer(raw)
    message = extract_message(raw)
    decision = extract_decision(raw)
    if offer is None:
        offer = fallback_offer
    if not message:
        message = raw[:1200]
    return message, offer, decision, raw