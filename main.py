"""Dog Guesser — interface Tkinter, dessinée avec un Canvas."""
import argparse
import math
import queue
import threading
import time
import tkinter as tk
import tkinter.font as tkfont

from PIL import Image, ImageTk, ImageOps

from game import (DATA, ROUNDS, TIME_LIMIT, label, load_breeds, load_question,
                  points, read_json, save_game)
from network import RecordsClient

BG = '#F3F0E7'
PAPER = '#FFFEF9'
INK = '#183D35'
MUTED = '#68776B'
ORANGE = '#EC7645'
LINE = '#DDDCD0'
GREEN = '#DCE8C8'
RED = '#F7DECF'


class DogGuesser:
    def __init__(self, root, server):
        self.root = root
        families = {name.lower() for name in tkfont.families(root)}
        self.font = next((name for name in ('Segoe UI', 'DejaVu Sans', 'Helvetica')
                          if name.lower() in families), 'Arial')
        root.title('Dog Guesser · Le flair du détail')
        root.geometry('1160x790')
        root.minsize(960, 780)
        root.configure(bg=BG)
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.events = queue.Queue()
        self.network = RecordsClient(server, self.events)
        self.screen = 'home'
        self.name = 'Joueur'
        self.name_var = tk.StringVar(value='')
        self.entry = None
        self.breeds = []
        self.question = None
        self.records = []
        self.connected = False
        self.score = self.correct = self.streak = self.round = 0
        self.answered = True
        self.loading = False
        self.message = ''
        self.sync_message = ''
        self.history = []
        self.started = 0
        self.photo = None
        self.photo_key = None
        self.last_size = None
        self.root.bind('<Configure>', self.resize)
        self.root.bind('<Key>', self.key)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.draw()
        self.root.after(80, self.poll)
        self.root.after(100, self.tick)
        threading.Thread(target=self.get_breeds, daemon=True).start()

    def close(self):
        self.network.stopped.set()
        self.root.destroy()

    def resize(self, event):
        if event.widget == self.root:
            size = (event.width, event.height)
            if size != self.last_size:
                self.last_size = size
                self.root.after_idle(self.draw)

    def text(self, x, y, value, size=12, color=INK, weight='normal', anchor='nw', **kwargs):
        return self.canvas.create_text(x, y, text=value, fill=color,
                                       font=(self.font, size, weight), anchor=anchor, **kwargs)

    def rect(self, x, y, w, h, fill, outline=''):
        return self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline=outline)

    def button(self, x, y, w, h, title, action, fill=INK, color=PAPER):
        tag = 'button' + str(len(self.canvas.find_all()))
        self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline='', tags=tag)
        self.canvas.create_text(x+20, y+h/2, text=title, fill=color,
                                font=(self.font, 12, 'bold'), anchor='w', width=w-36, tags=tag)
        self.canvas.tag_bind(tag, '<Button-1>', lambda event: action())
        self.canvas.tag_bind(tag, '<Enter>', lambda event: self.canvas.configure(cursor='hand2'))
        self.canvas.tag_bind(tag, '<Leave>', lambda event: self.canvas.configure(cursor=''))

    def paw(self, x, y, scale=1, color=INK):
        for dx, dy, r in [(-15,-12,6),(-4,-20,6),(9,-18,6),(19,-7,6),(1,5,13)]:
            self.canvas.create_oval(x+(dx-r)*scale, y+(dy-r)*scale,
                                    x+(dx+r)*scale, y+(dy+r)*scale, fill=color, outline='')

    def photo_at(self, image, x, y, w, h):
        # ImageOps.contain conserve tout le chien, y compris ses oreilles et ses pattes.
        key = (id(image), int(w), int(h))
        if key != self.photo_key:
            fitted = ImageOps.contain(image, (int(w), int(h)), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(fitted)
            self.photo_key = key
        self.rect(x,y,w,h,'#E8E5D9')
        self.canvas.create_image(x+w/2,y+h/2,image=self.photo)

    def draw(self):
        if not self.root.winfo_exists():
            return
        self.canvas.delete('all')
        self.canvas.configure(cursor='')
        w = max(960, self.canvas.winfo_width())
        h = max(780, self.canvas.winfo_height())
        self.width, self.height = w, h
        self.paw(52,43,0.7)
        self.text(83,25,'DOG GUESSER',18,weight='bold')
        self.text(84,53,'LE FLAIR DU DÉTAIL',9,color=MUTED)
        self.text(w-36,34, '●  Records connectés' if self.connected else '○  Records hors ligne',
                  10,color=INK if self.connected else MUTED,anchor='ne')
        self.rect(32,83,w-64,1,LINE)
        if self.screen == 'home':
            self.draw_home(w,h)
        elif self.screen == 'play':
            self.draw_play(w,h)
        else:
            self.draw_result(w,h)
        self.rect(32,h-48,w-64,1,LINE)
        self.text(36,h-32,'PHOTOS : DOG CEO  /  10 MANCHES · 20 S PAR PHOTO',9,color=MUTED)
        self.text(w-36,h-32,'Un œil affûté. Un bon flair.',9,color=MUTED,anchor='ne')

    def draw_home(self,w,h):
        split = int(w*0.52)
        self.text(48,116,'LE QUIZ QUI A DU CHIEN',10,color=ORANGE,weight='bold')
        self.text(44,153,'Tu as du flair ?',34,weight='bold')
        self.text(48,218,'Une photo. Quatre races.\nÀ toi de trouver la bonne.',17,color=MUTED)
        self.text(48,302,'01  Observe      02  Choisis      03  Bats ton record',11)
        self.text(48,355,'TON PSEUDO',10,weight='bold')
        if self.entry is None:
            self.entry = tk.Entry(self.root,textvariable=self.name_var,font=(self.font,14),
                                  bg=PAPER,fg=INK,insertbackground=INK,relief='flat',highlightthickness=1,
                                  highlightbackground=LINE,highlightcolor=ORANGE)
        self.canvas.create_window(48,381,window=self.entry,anchor='nw',width=split-104,height=48)
        self.button(48,449,split-104,54,'C’est parti  →',self.start)
        self.text(48,524,'+100 par bonne réponse, bonus de vitesse et de série.',10,color=MUTED,
                  width=split-100)
        self.text(48,569,self.message or 'Les records se mettent à jour entre tous les joueurs.',10,
                  color=ORANGE if self.message else MUTED,width=split-100)
        x = split+10
        pw,ph = w-x-40,h-210
        if self.question:
            self.photo_at(self.question['image'],x,110,pw,ph)
        else:
            self.rect(x,110,pw,ph,GREEN)
            self.paw(x+pw/2,110+ph/2,3.8)
            self.text(x+pw/2,110+ph/2+110,'Le prochain museau arrive…',12,anchor='n')
        self.rect(x+14,124,150,30,INK)
        self.text(x+26,131,'100 % DOG LOVER',9,color=PAPER,weight='bold')
        self.rect(x,110+ph-60,pw,60,INK)
        self.text(x+20,110+ph-44,'DIX PHOTOS. UN SEUL DÉFI.',12,color=PAPER,weight='bold')
        self.text(x+20,110+ph-22,'Reconnaîtras-tu chaque race ?',10,color='#D4DFCB')

    def draw_play(self,w,h):
        self.text(36,105,f'MANCHE {self.round:02d} / {ROUNDS}',10,weight='bold')
        self.text(w-36,103,f'{self.score:,} pts'.replace(',',' '),18,weight='bold',anchor='ne')
        photo_w = int((w-100)*0.57)
        photo_h = h-370
        x = photo_w+64
        right_w = w-x-36
        if self.question:
            self.photo_at(self.question['image'],36,148,photo_w,photo_h)
        else:
            self.rect(36,148,photo_w,photo_h,GREEN)
            self.paw(36+photo_w/2,148+photo_h/2,2)
        if self.loading:
            self.rect(36,148,photo_w,photo_h,BG)
            self.text(36+photo_w/2,148+photo_h/2,'À la recherche du prochain chien…',13,anchor='center')
        self.text(x,148,'À QUI CE MUSEAU ?',10,color=ORANGE,weight='bold')
        self.text(x,176,'Quelle est sa race ?',22,weight='bold')
        self.text(x,220,'Choisis une réponse · touches 1 à 4',10,color=MUTED)
        if self.question and not self.loading:
            for i,breed in enumerate(self.question['choices']):
                fill,color = PAPER,INK
                if self.answered and breed == self.question['breed']:
                    fill=GREEN
                elif self.answered and breed == self.selected:
                    fill=RED
                title = f'{i+1}   {label(breed)}'
                if self.answered and breed == self.question['breed']:
                    title += '  ✓'
                self.button(x,255+i*57,right_w,47,title,lambda i=i:self.answer(i),fill,color)
        y = 148+photo_h+16
        if self.loading:
            self.text(36,y,self.message or 'Chargement de la photo…',11,color=MUTED)
            if self.message:
                self.button(x,492,right_w,44,'Réessayer →',self.next_question)
        elif self.answered:
            self.text(36,y,self.message,12,weight='bold',width=photo_w)
            self.button(x,492,right_w,44,'Voir mon résultat →' if self.round == ROUNDS else 'Photo suivante →',
                        self.finish if self.round==ROUNDS else self.next_question)
        else:
            self.canvas.create_text(36,y,text='',fill=INK,font=(self.font,12,'bold'),
                                    anchor='nw',tags='timer-label')
            self.rect(36,y+30,photo_w,6,LINE)
            self.canvas.create_rectangle(36,y+30,36+photo_w,y+36,fill=ORANGE,outline='',tags='timer-bar')
            self.text(x,492,f'SÉRIE : {self.streak} bonne(s) réponse(s)',10,color=MUTED)
            self.update_timer()
        self.draw_board(36,h-142,w-72)

    def draw_board(self,x,y,width):
        self.rect(x,y,width,77,INK)
        self.text(x+18,y+14,'LE PODIUM',10,color='#D4DFCB',weight='bold')
        if not self.records:
            self.text(x+18,y+40,'Pas encore de record. À toi d’ouvrir le classement !',11,color=PAPER)
        else:
            cell=(width-150)/3
            for i,r in enumerate(self.records[:3]):
                xx=x+145+i*cell
                self.text(xx,y+14,f'{i+1:02d}  {r["name"]}',11,color=PAPER,weight='bold')
                self.text(xx,y+40,f'{r["score"]} points',11,color='#D4DFCB')

    def draw_result(self,w,h):
        self.text(w/2,114,'BIEN JOUÉ, '+self.name.upper(),11,color=ORANGE,weight='bold',anchor='n')
        self.text(w/2,150,'Un flair à entraîner.' if self.correct<5 else 'Tu as du chien !',30,weight='bold',anchor='n')
        self.text(w/2,208,f'{self.score} points',42,weight='bold',anchor='n')
        self.text(w/2,283,f'{self.correct} / {ROUNDS} bonnes réponses',15,color=MUTED,anchor='n')
        history=read_json(DATA/'scores.json')
        best=max((r.get('score',0) for r in history if r.get('name')==self.name),default=0)
        self.text(w/2,323,f'Record personnel : {best} pts  ·  {self.sync_message}',10,color=MUTED,anchor='n')
        # Un récapitulatif court aide à apprendre les races manquées.
        colw=(w-100)/2
        for i,item in enumerate(self.history):
            col,row=i//5,i%5
            marker='✓' if item['correct'] else '×'
            self.text(50+col*colw,370+row*29,f'{i+1:02d}  {marker}  {label(item["breed"])}',11,
                      color=INK if item['correct'] else MUTED)
        self.button(w/2-225,535,215,48,'Rejouer →',self.start)
        self.button(w/2+10,535,215,48,'Changer de pseudo',self.home,GREEN,INK)
        self.draw_board(36,h-142,w-72)

    def home(self):
        self.screen='home'
        self.message=''
        self.draw()

    def start(self):
        if self.loading:
            return
        if not self.breeds:
            self.message='Connexion à Dog CEO impossible. Clique pour réessayer.'
            threading.Thread(target=self.get_breeds,daemon=True).start()
            self.draw()
            return
        self.name=(self.name_var.get().strip() or 'Joueur')[:20]
        self.name_var.set(self.name)
        if self.entry is not None:
            self.entry.destroy()
            self.entry=None
        self.screen='play'
        self.score=self.correct=self.streak=self.round=0
        self.history=[]
        self.next_question()

    def get_breeds(self):
        try:
            breeds=load_breeds()
            self.events.put(('breeds',breeds))
            self.events.put(('cover',load_question(breeds)))
        except Exception:
            self.events.put(('api_error','Dog CEO est inaccessible. Vérifie ta connexion puis réessaie.'))

    def next_question(self):
        if self.loading and not self.message:
            return
        self.loading=True
        self.answered=True
        self.message=''
        self.draw()
        def worker():
            try:
                self.events.put(('question',load_question(self.breeds)))
            except Exception:
                self.events.put(('api_error','Photo indisponible. Tu peux réessayer sans perdre de point.'))
        threading.Thread(target=worker,daemon=True).start()

    def answer(self,index):
        if self.screen!='play' or self.answered or self.loading:
            return
        elapsed=time.monotonic()-self.started
        self.selected=self.question['choices'][index] if index is not None and elapsed<TIME_LIMIT else None
        good=self.selected==self.question['breed']
        self.streak=self.streak+1 if good else 0
        gain=points(good,elapsed,self.streak)
        self.score+=gain
        self.correct+=int(good)
        self.answered=True
        self.history.append({'breed':self.question['breed'],'correct':good})
        self.message=(f'Bien vu ! +{gain} points' if good else
                      ('Temps écoulé. ' if self.selected is None else 'Raté ! ')+
                      'C’était : '+label(self.question['breed']))
        self.draw()

    def finish(self):
        if self.screen!='play' or not self.answered or self.round!=ROUNDS:
            return
        try:
            record=save_game(self.name,self.score,self.correct)
            self.sync_message='Score sauvegardé sur ce PC'
        except OSError:
            self.sync_message='Échec de la sauvegarde locale (dossier non accessible)'
            record={'name':self.name,'score':self.score,'correct':self.correct}
        self.network.submit(record)
        if not self.connected:
            self.sync_message+=' · en attente du serveur'
        self.screen='result'
        self.draw()

    def key(self,event):
        if self.screen=='play' and event.char in ('1','2','3','4'):
            self.answer(int(event.char)-1)
        elif event.keysym=='Return':
            if self.screen=='home': self.start()
            elif self.screen=='result': self.start()
            elif self.answered and not self.loading:
                self.finish() if self.round==ROUNDS else self.next_question()

    def update_timer(self):
        remaining=max(0,TIME_LIMIT-(time.monotonic()-self.started))
        self.canvas.itemconfigure('timer-label',text=f'{math.ceil(remaining):02d} s restantes  ·  Le chrono joue pour toi.')
        width=int((self.width-100)*0.57)
        y=148+self.height-370+46
        self.canvas.coords('timer-bar',36,y,36+width*remaining/TIME_LIMIT,y+6)

    def tick(self):
        if self.screen=='play' and not self.loading and not self.answered:
            self.update_timer()
            if time.monotonic()-self.started>=TIME_LIMIT:
                self.answer(None)
        self.root.after(100,self.tick)

    def poll(self):
        redraw=False
        while not self.events.empty():
            kind,data=self.events.get_nowait()
            if kind=='breeds': self.breeds=data
            elif kind=='cover':
                if self.screen=='home': self.question=data; redraw=True
            elif kind=='question':
                self.question=data
                self.photo_key=None
                self.loading=False
                self.answered=False
                self.selected=None
                self.round+=1
                self.started=time.monotonic()
                redraw=True
            elif kind=='api_error': self.message=data; redraw=True
            elif kind=='connection':
                redraw=self.connected!=data or redraw
                self.connected=data
            elif kind=='records': self.records=data; redraw=True
            elif kind=='sync':
                self.sync_message='Score enregistré sur le serveur' if data else 'Score refusé par le serveur'
                redraw=True
        if redraw: self.draw()
        self.root.after(80,self.poll)


def main():
    parser=argparse.ArgumentParser(description='Dog Guesser')
    parser.add_argument('--server',default='ws://127.0.0.1:8765')
    args=parser.parse_args()
    root=tk.Tk()
    DogGuesser(root,args.server)
    root.mainloop()


if __name__=='__main__':
    main()
