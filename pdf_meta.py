#!/bin/env pyton
# coding:utf8

#Forensique Tool

import PyPDF2 # pip install
import argparse 
import re 
import exifread # pip install
import sqlite3

#____ARGUMENTS____
parser = argparse.ArgumentParser(description="Outil Forensique")
parser.add_argument("-pdf", dest="pdf", help="Chemin du fichier PDF", required=False)
# python pdf_meta.py -pdf ANONOPS_The_Press_Release.pdf
parser.add_argument("-str", dest="str", help="Chemin du fichier ou recuperer les chaines de caracteres", required=False)
# python pdf_meta.py -str ANONOPS_The_Press_Release.pdf
parser.add_argument("-exif", dest="exif", help="Chemin de l'image pour recuprer meta exif", required=False)
# python pdf_meta.py -str ANONOPS_The_Press_Release.pdf
parser.add_argument("-gps", dest="gps", help="Recuperer coordonnées image si existante", required=False)
# python pdf_meta.py -gps mcafee.jpg
parser.add_argument("-fh", dest="fhistory", help="Recuperer les sites visité dans firefox depuis fichier places.sqlite", required=False)
# python pdf_meta.py -fh places.sqlite
parser.add_argument("-fc", dest="fcookies", help="Recuperer les cookies dans firefox depuis fichier cookies.sqlite", required=False)
# python pdf_meta.py -fc cookies.sqlite
args = parser.parse_args()

#____PROTOTYPE____
def get_pdf_meta(file_name):
    """Meta basique
Obetnir une meta basique tel qu'on l'a trouve dans les proprietés d'un pdf
    Args:
        file_name (pdf): Fichier ou chemin
    """
    pdf_file = PyPDF2.PdfReader(open(file_name,"rb"))  
    doc_info = pdf_file.getDocumentInfo()                      
    for info in doc_info:
        print("[+]", info + " " + doc_info[info])      
        
def get_strings(file_name):
    """Meta + RegEx
#1
Iterer selon RegEx pour meta plus precise : Dans le rendu du terminal on peut constater par exemple vers la fin
<</Author<FEFF0041006C0065007800200054006100700061006E0061007200690073>
/Creator<FEFF005700720069007400650072>
/Producer<FEFF004F00700065006E004F00660066006900630065002E006F0072006700200033002E0032>
/CreationDate(D:20101210031827+02'00')>>

Les caractere entre <"> est du UTF16
Pour fair la traduction on peut ouvrir la console python :
bytes.fromhex("FEFF0041006C0065007800200054006100700061006E0061007200690073").decode("utf16")
resultat > 'Alex Tapanaris'

    Args:
        file_name (pdf): Fichier ou chemin
    """
    with open(file_name,"rb") as file : 
        content = file.read()   
    _re = re.compile("[\S\s]{4,}")      # Etudier le RegEx
    for match in _re.finditer(content.decode("utf8", "backslashreplace")): #1
    # match = _re.findall(content.decode("utf8", "backslashreplace"))   
        print(match.group())

def get_exif(file_name):
    """EXIF FILE
Permet de recuperer metadonnées d'une photo
    Args:
        file_name (multi): Fichier photo png, jpeg etc
    """
    with open(file_name, "rb") as file : 
        exif = exifread.process_file(file)
        print(exif)
    if not exif : 
        print("Aucune metadonnées EXIF")
    else : 
        for tag in exif.keys():               # On peut constater l'affichage des tag dans le terminal, on peut recuperer ces tag pour les afficher ensuite dans le print grace au get
            print(tag + " " + str(exif[tag]))      # via une liste on peut iterer sur les tag , il faut pas oublier de str sur le exif[tag]

def _convert_to_degress(value):
    """Convertion des Long/Lat en en coordonnées exploitable 
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0)

def get_gps_from_exif(file_name):
    with open(file_name, "rb") as file : 
        exif = exifread.process_file(file)
        # print(exif)
    if not exif : 
        print("Aucune metadonnées EXIF")
    else : 
        latitude = exif.get("GPS GPSLatitude")
        latitude_ref = exif.get("GPS GPSLatitudeRef")
        longitude = exif.get("GPS GPSLongitude")
        longitude_ref = exif.get("GPS GPSLongitudeRef")
        altitude = exif.get("GPS GPSAltitude")
        altitude_ref = exif.get("GPS GPSAltitudeRef")
        # print(str(latitude) + str(longitude))
        if latitude and longitude and latitude_ref and longitude_ref : # Si coordonnées existant convertir en coordonnées inerpretable/compresehensible 
            lat = _convert_to_degress(latitude)
            long = _convert_to_degress(longitude)
            # print(str(lat) +" "+ str(long))
            if str(latitude_ref) != "N":                                # standar 
                lat = 0 - lat 
            if str(longitude_ref) != "E":
                long = 0 - long 
            print()
            print("Latitude :" + str(lat) + " Longitude : " + str(long)) # Il est possible de gglisser le la localisation dans une requete HTTP google 
            print()
            print("URL : http://maps.google.com/maps?q=loc:%s,%s" % (str(lat) , str(long)))
            print()
            if altitude and altitude_ref : 
                alt_ = altitude.values[0]
                alt = alt_.num / alt_.den
                if altitude_ref.values[0] == 1 :
                    alt = 0 - alt
                print("Altitude : " + str(alt))
                print()
           
def get_firefox_history(places_sqlite):
    """Requete SQL Firefox
Permet de requete un fichier de cookies par exemple a condition de connaitre sont architecture table/clé ...., ici nous ciblon un navigateur Firefox 
    Args:
        places_sqlite (_type_): _description_
    """
    try :
        conn = sqlite3.connect(places_sqlite)
        cursor = conn.cursor()
        cursor.execute("SELECT url, datetime(last_visit_date/1000000, \"unixepoch\") FROM moz_places, moz_historyvisits WHERE visit_count > 0 AND moz_places.id == moz_historyvisits.place_id")     # *-* unixepoch > facon incremental de notifier une date et heure ...
        # print(cursor.fetchall())       # Apercu du resultat
        header = "<!DOCTYPE html><head><style>table,th,tr,td{border:1px solid black;}</style></head><body><table><tr><th>URL</th><th>Date</th></tr>" # ---     Integration balise web pour un mise en page
        with open("rapport_firefox_historique.html" , "a") as f:
            f.write(header)
            for row in cursor:
                url = str(row[0])
                date = str(row[1])
                f.write("<tr><td><a href ='" + url + "'>" + url +"</a></td><td>" + date + "</td></tr>")
            footer = "</table></body></html>"                                                       #--- 1
            f.write(footer)
        # print("[+] " + url + " " + date) #---1     # affichage de la date "http://cyberini.com/ >> 1589829004467000 " en time stemp, il faut le traiter, il faut donc modifier la raquete sql plus haut *-*
    
    except Exception as e :
        print("[-] Erreur : " + str(e))
        exit(1)
        
def get_firefox_cookies(cookies_sqlite):
    """Cookies Firefox

    Args:
        cookies_sqlite (SQL): Exploiter cookies firefox
    """
    try :
        conn = sqlite3.connect(cookies_sqlite)
        cursor = conn.cursor()
        # cursor.execute("SELECT name FROM sqlite_master WHERE type='table'") # afficher les tables dispo avec nalme à la place de moz_c pour appercu
        # print(cursor.fetchone())  # ou fetchall pour avoir un apercu
        # print(cursor.decription) # info ou on voit la clé des valeur
        # cursor.execute("SELECT * FROM moz_cookies ") # afficher les tables dispo avec nalme à la place de moz_c pour appercu
        cursor.execute("SELECT name, value,host FROM moz_cookies ")
        header = "<!DOCTYPE html><head><style>table,th,tr,td{border:1px solid black;}</style></head><body><table><tr><th>Nom cookie</th><th>Valeur cookie</th></tr>"
        with open("rapport_firefox_cookies.html" , "a") as f:
            f.write(header)
            for row in cursor:
                name = str(row[0])
                value = str(row[1])
                host = str(row[2])
                f.write("<tr><td>" + name + "</td><td>" + value + "</td><td>" + host + "</td></tr>")
            footer = "</table></body></html>"                                                 
            f.write(footer)
    
    except Exception as e :
        print("[-] Erreur : " + str(e))
        exit(1)


#____MAIN____
if args.pdf:
    get_pdf_meta(args.pdf)
if args.str:
    get_strings(args.str)
if args.exif:
    get_exif(args.exif)
if args.gps:
    get_gps_from_exif(args.gps)
if args.fhistory:
    get_firefox_history(args.fhistory)
if args.fcookies:
    get_firefox_cookies(args.fcookies)
