"""Règles, appels à Dog CEO et sauvegarde des parties."""
import json
import random
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image
from io import BytesIO

ROUNDS = 10
TIME_LIMIT = 20
API = 'https://dog.ceo/api'
DATA = Path(__file__).resolve().parent / 'data'

# Les noms non traduits restent ceux de l'API, sans inventer de traduction.
NAMES = {
    'german-shepherd': 'Berger allemand', 'retriever-golden': 'Golden retriever',
    'bulldog-french': 'Bouledogue français', 'bulldog-english': 'Bulldog anglais',
    'mountain-bernese': 'Bouvier bernois', 'dachshund': 'Teckel',
    'pug': 'Carlin', 'poodle-standard': 'Caniche royal',
    'poodle-toy': 'Caniche toy', 'poodle-miniature': 'Caniche miniature',
    'spaniel-cocker': 'Cocker', 'terrier-yorkshire': 'Yorkshire terrier',
    'dane-great': 'Dogue allemand', 'newfoundland': 'Terre-neuve',
    'frise-bichon': 'Bichon frisé', 'collie-border': 'Border collie',
    'shiba': 'Shiba inu', 'stbernard': 'Saint-bernard',
    'husky': 'Husky', 'labrador': 'Labrador', 'beagle': 'Beagle',
    'dalmatian': 'Dalmatien', 'samoyed': 'Samoyède', 'malinois': 'Malinois',
}


def label(breed):
    return NAMES.get(breed, breed.replace('-', ' ').title())


def api_get(endpoint):
    response = requests.get(API + endpoint, timeout=(5, 15))
    response.raise_for_status()
    data = response.json()
    if data.get('status') != 'success':
        raise ValueError('Dog CEO ne renvoie pas de données utilisables.')
    return data['message']


def load_breeds():
    breeds = []
    for parent, children in api_get('/breeds/list/all').items():
        if children:
            breeds.extend(parent + '-' + child for child in children)
        else:
            breeds.append(parent)
    if len(breeds) < 4:
        raise ValueError('Il faut au moins quatre races pour jouer.')
    return breeds


def load_question(breeds):
    url = api_get('/breeds/image/random')
    breed = url.split('/breeds/')[1].split('/')[0]
    if breed not in breeds:
        raise ValueError('La race de cette photo est inconnue. Réessaie.')
    choices = random.sample([b for b in breeds if b != breed], 3) + [breed]
    random.shuffle(choices)
    response = requests.get(url, timeout=(5, 15))
    response.raise_for_status()
    picture = Image.open(BytesIO(response.content)).convert('RGB')
    return {'breed': breed, 'choices': choices, 'image': picture, 'url': url}


def points(correct, elapsed, streak):
    if not correct:
        return 0
    speed = int(max(0, TIME_LIMIT - elapsed) * 10)
    combo = min(max(streak - 1, 0), 4) * 25
    return 100 + speed + combo


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def save_game(name, score, correct):
    record = {'name': name, 'score': score, 'correct': correct,
              'date': datetime.now().isoformat(timespec='seconds')}
    history = read_json(DATA / 'scores.json')
    history.append(record)
    write_json(DATA / 'scores.json', history)
    return record
