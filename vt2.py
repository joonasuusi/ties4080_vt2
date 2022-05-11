# -*- coding: utf-8 -*-

# from flask_wtf import FlaskForm #tämä versio ei ole xml-yhteensopiva
from flask_wtf_polyglot import PolyglotForm 
#tämä tuottaa xml-yhteensopivia lomakekenttiä
from wtforms import Form, BooleanField, StringField, validators, IntegerField, SelectField, widgets, SelectMultipleField, ValidationError, FieldList, FormField
from flask import Flask, render_template, Response, request, redirect, url_for
from jinja2 import Template, Environment, FileSystemLoader
from flask_wtf.csrf import CSRFProtect
import urllib.request
import simplejson as json
import os

app = Flask(__name__)

app.secret_key = '"\xf9$T\x88\xefT8[\xf1\xc4Y-r@\t\xec!5d\xf9\xcc\xa2\xaa'

# Luo listan jonka mukaan tehdään pelilauta
def teeLista(vari1, vari2, n):
    lista = [[0 for i in range(n)] for j in range(n)]
    for i in range(n):
        for j in range(n):
            if i%2 == 0:
                if j%2 == 0:
                    lista[i][j] = vari1
                else:
                    lista[i][j] = vari2
            if i%2 != 0:
                if j%2 != 0:
                    lista[i][j] = vari1
                else:
                    lista[i][j] = vari2
    return lista

# tarkistaa syötettyjen pelaajien niumen pituuden onko validi
def my_length_check(form, field):
    if len(field.data.strip()) < 1:
        raise ValidationError('Liian lyhyt nimi')

# Ladataan json data jota käytetään pelilaudan koon/pallojen suunnan/laattojen värijärjestyksen määrittelyyn
def lataaData():
    with urllib.request.urlopen('https://europe-west1-ties4080.cloudfunctions.net/vt2_taso1') as response:
        data = json.load(response)
    return data


def teePallot(n):
    pallot = [0 for i in range(n)]
    return pallot

# Pääreitti ohjelmaan
@app.route('/', methods=['POST','GET']) 
def lomake():
    data = lataaData() 
    print(data)
    minkoko = data.get('min')
    maxkoko = data.get('max')
    ekavari = data.get('first')  # td1 = valkoinen & td2 = musta
    suunta = data.get('balls')
    
    n = int(request.form.get("pelilauta", minkoko))
    if request.args.get("x"): # jos url parametri annettu saadaan oikea koko ja oikeat pallon määrät
        n = int(request.args.get("x"))
    
    pallot = teePallot(n)
    for i in range(len(pallot)): # apulista pallojen tekoon
        pallot[i] = i

    if suunta == "bottom-to-top": # tarkistetaan suunta pallojen tekoa varten
        pallot.reverse()
    try:
        indeksi = request.form.get("napinpoisto") # jos jo poistettu palloja 
        pallot[int(indeksi)-1] = ''
    except:
        pass
    #pallot[2] = ''
    print(pallot)
    linkki = False # asetetaan linkki ensiksi inaktiiviseksi
    if suunta == "top-to-bottom":
        pallot = pallot
    
    if ekavari == "black":
        valko = 'td2'
        musta = 'td1'
        lista = teeLista(valko, musta, n)
    else:
        valko = 'td1'
        musta = 'td2'
        lista = teeLista(valko, musta, n)
    
    class pelaajat(PolyglotForm): # Luokka pelaajia/pelilaudan koko varten
        pelilauta    = IntegerField('Laudan koko',id="koko", default=minkoko, widget = widgets.Input(input_type="number"), validators=[validators.NumberRange(min=minkoko, max=maxkoko, message="Syöttämäsi arvo ei kelpaa")])
        pelaaja1     = StringField('Pelaaja 1', validators=[validators.InputRequired(), my_length_check])
        pelaaja2     = StringField('Pelaaja 2', validators=[validators.InputRequired(), my_length_check])

    # luodaan formi
    form = pelaajat()
    peluri1 = request.form.get("pelaaja1")
    peluri2 = request.form.get("pelaaja2")
    poisto = ""
    if peluri1 == None:
        peluri1 = ""
    if peluri2 == None:
        peluri2 = ""
    if request.method == 'POST':
        try: # tarkistetaan onko pallon poisto kysessä
            if request.form.get('pallonappi'):
                elementti = request.form.get('pallonappi')
                poisto = request.form.get("napinpoisto")
                pallot_index = 0
                pallot_index_alaspain = n-1
                if suunta == "bottom-to-top":
                    poisto = poisto[::-1]
                print(poisto,"käännetty")
                for i in range(len(poisto)):
                    #print(poisto[i])
                    # Tehdään tyhjä paikka pallot listaan jotta sinistä palloa ei tule indeksiin
                    if poisto[i] == "'" and poisto[i+1] == "'":
                        pallot[pallot_index] = ''
                        pallot_index += 1
                    try:
                        # tsekataan poistolistaa ja jos totta niin pallot listaan oikea indeksi mihin sininen pallo tulee
                        if int(poisto[i]) <= n:
                            arvo = int(poisto[i])
                            print(pallot[pallot_index])
                            #if pallot[i] != '':
                            pallot[pallot_index] = pallot_index
                            pallot_index += 1
                        else:
                            continue
                    except:
                        pass
                if suunta == "bottom-to-top":
                    pallot.reverse()
                pallot[int(elementti)-1] = ''
                #poisto = pallot
        except:
            poisto = ""
        # kikkailu saada Undo linkki aktiiviseksi, eli jos yksikin on poistettu
        if '' in pallot:
            linkki = True
        form.validate()
        if n < minkoko or n > maxkoko or len(peluri1.strip()) < 1 or len(peluri2.strip()) < 1:
            lista = teeLista('','',0)
            peluri1 = ""
            peluri2 = ""

    # onko url parametreja, jos on niin tehdään pelilauta niiden mukaan
    if request.args.get("x") and request.args.get("pelaaja1") and request.args.get("pelaaja2"):
        n = int(request.args.get("x"))
        peluri1 = request.args.get("pelaaja1")
        peluri2 = request.args.get("pelaaja2")
        
        if n >= minkoko and n <= maxkoko:
            lista = teeLista(valko, musta, n)
        else:
            lista = teeLista('', '', 0)
            peluri1 = ""
            peluri2 = ""
        
        return Response(render_template('pohja.xhtml', form=form, lista=lista, peluri1=peluri1, peluri2=peluri2, pallot=pallot, poisto=poisto, linkki=linkki), mimetype="application/xhtml+xml")
    return Response(render_template('pohja.xhtml', form=form, lista=lista, peluri1=peluri1, peluri2=peluri2, pallot=pallot, poisto=poisto, linkki=linkki), mimetype="application/xhtml+xml")
