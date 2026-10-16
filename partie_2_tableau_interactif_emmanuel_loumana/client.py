"""Client en terminal : saisie des formes et envoi à POST /draw."""
import argparse
import requests

FORMES = {
    '1': ('point', ('x', 'y')),
    '2': ('line', ('x1', 'y1', 'x2', 'y2')),
    '3': ('circle', ('x', 'y', 'radius')),
    '4': ('rectangle', ('x', 'y', 'width', 'height')),
    '5': ('square', ('x', 'y', 'cote')),
}
LABELS = {'radius': 'rayon', 'width': 'largeur', 'height': 'hauteur', 'cote': 'côté'}


def send(base_url, endpoint, data=None):
    try:
        response = requests.post(base_url.rstrip('/') + endpoint, json=data, timeout=5)
        response.raise_for_status()
        return True
    except requests.HTTPError as error:
        try:
            message = error.response.json().get('error', str(error))
        except ValueError:
            message = str(error)
        print('Refus du serveur :', message)
    except requests.RequestException:
        print('Serveur inaccessible. Vérifie son adresse et son lancement.')
    return False


def ask_number(field):
    maximum = 640 if field in ('y', 'y1', 'y2', 'height') else 1000
    minimum = 0 if field in ('x', 'y', 'x1', 'y1', 'x2', 'y2') else 0.01
    while True:
        try:
            value = float(input(f'  {LABELS.get(field, field)} ({minimum} à {maximum}) : ').replace(',', '.'))
            if minimum <= value <= maximum:
                return value
        except ValueError:
            pass
        print('  Entre un nombre dans cet intervalle.')


def ask_color():
    while True:
        raw = input('  Couleur R,V,B [43,119,107] : ').strip() or '43,119,107'
        try:
            color = [int(value.strip()) for value in raw.split(',')]
            if len(color) == 3 and all(0 <= value <= 255 for value in color):
                return color
        except ValueError:
            pass
        print('  Exemple : 236,118,69. Trois entiers entre 0 et 255.')


def example():
    # Un petit paysage composé uniquement des cinq formes du sujet.
    return [
        {'shape':'rectangle', 'x':0, 'y':480, 'width':1000, 'height':160, 'color':[220,232,200]},
        {'shape':'circle', 'x':790, 'y':135, 'radius':65, 'color':[238,184,82]},
        {'shape':'rectangle', 'x':330, 'y':280, 'width':300, 'height':225, 'color':[233,192,152]},
        {'shape':'line', 'x1':305, 'y1':280, 'x2':480, 'y2':145, 'color':[43,119,107]},
        {'shape':'line', 'x1':480, 'y1':145, 'x2':655, 'y2':280, 'color':[43,119,107]},
        {'shape':'square', 'x':370, 'y':325, 'cote':65, 'color':[255,254,249]},
        {'shape':'square', 'x':520, 'y':325, 'cote':65, 'color':[255,254,249]},
        {'shape':'rectangle', 'x':455, 'y':400, 'width':60, 'height':105, 'color':[43,119,107]},
        {'shape':'point', 'x':500, 'y':457, 'color':[238,184,82]},
        {'shape':'rectangle', 'x':170, 'y':355, 'width':22, 'height':150, 'color':[169,126,96]},
        {'shape':'circle', 'x':181, 'y':320, 'radius':70, 'color':[43,119,107]},
        {'shape':'circle', 'x':230, 'y':345, 'radius':45, 'color':[92,151,123]},
    ]


def run(base_url):
    print('\nATELIER COMMUN — client de dessin')
    print('Tableau de 1000 × 640. Origine (0,0) en haut à gauche.')
    print('Pour les cercles, x et y désignent le centre ; pour les rectangles et carrés, le coin supérieur gauche.')
    print('Les formes peuvent dépasser du tableau : la partie extérieure est masquée.')
    try:
        while True:
            print('\n1 Point · 2 Ligne · 3 Cercle · 4 Rectangle · 5 Carré')
            print('6 Dessin d’exemple · 7 Effacer le tableau · 0 Quitter')
            choice = input('Ton choix : ').strip()
            if choice == '0':
                return
            if choice == '6':
                count = 0
                for shape in example():
                    if not send(base_url, '/draw', shape):
                        break
                    count += 1
                print(f'{count} forme(s) envoyée(s).')
            elif choice == '7':
                if input('Effacer pour tous les joueurs ? (o/N) : ').strip().lower() == 'o':
                    if send(base_url, '/clear'):
                        print('Tableau effacé.')
            elif choice in FORMES:
                kind, fields = FORMES[choice]
                data = {'shape': kind}
                for field in fields:
                    data[field] = ask_number(field)
                data['color'] = ask_color()
                if send(base_url, '/draw', data):
                    print('Forme envoyée au tableau.')
            else:
                print('Choisis un numéro du menu.')
    except (KeyboardInterrupt, EOFError):
        print('\nClient fermé.')


def main():
    parser = argparse.ArgumentParser(description='Client du tableau interactif')
    parser.add_argument('--server', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    run(args.server)


if __name__ == '__main__':
    main()
