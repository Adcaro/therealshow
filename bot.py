
# This file contains the source code of The Real Show Telegram Bot.
from telegram.ext import Updater, CommandHandler
import xml.etree.ElementTree as ET
import random
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('AchicaynaBot')

#clase de jugador
class Jugador(object):
    '''
    classdocs
    '''


    def __init__(n, g, a, ga, pe):
        '''
        Constructor
        '''
        self.nombre = n
        self.goles = g
        self.asistencias = a
        self.ganados = ga
        self.perdidos = pe

    def getNombre(self):
        return str(self.nombre)

#Metodo para leer jugadores y sus estadisticas
def leerJugadores():

        # parse an xml file by name
        with open('stats.xml', 'r', encoding='latin-1') as utf8_file:
            tree = ET.parse('stats.xml')

        for jugador in tree.findall("jugador"):
            nombre = jugador[0].text
            goles = jugador[1].text
            asistencias = jugador[2].text
            ganados = jugador[3].text
            perdidos = jugador[4].text

            jugador = Jugador(nombre, goles, asistencias, ganados, perdidos)
            jugadores[nombre] = jugador

#Metodo para introducir un jugador
def introducirJugador(nombre, goles, asistencias, ganados, perdidos):
        with open('stats.xml', 'r', encoding='latin-1') as utf8_file:
            tree = ET.parse(utf8_file)
        root = tree.getroot()
        jug = ET.Element("jugador")

        nomb = ET.SubElement(jug, "nombre")
        nomb.text = nombre

        gol = ET.SubElement(jug, "goles")
        gol.text = goles

        asist = ET.SubElement(jug, "asistencias")
        asist.text=asistencias

        gan = ET.SubElement(jug, "ganados")
        gan.text=ganados

        juga = ET.SubElement(jug, "jugados")
        juga.text=jugados

        root.insert(1, jug)

        tree.write('stats.xml')

#Metodo para introducir stats de un jugador
def addStatJugador(nombre, goles, asistencias, gano):
    with open('stats.xml', 'r', encoding='latin-1') as utf8_file:
        tree = ET.parse(utf8_file)
    root = tree.getroot()
    jugadores = root.findall('jugador')
    for jugador in jugadores:
        if(jugador[0].text == nombre):
            jugador[1].text = str(int(jugador[1].text) +goles)
            jugador[2].text = str(int(jugador[2].text) +asistencias)
            if(gano == 1):
                jugador[3].text = str(int(jugador[3].text) + 1)
            else:
                jugador[4].text = str(int(jugador[4].text) + 1)
    tree.write('stats.xml')
    


#Comandos del bot
#Comando para mostrar las stats
def stats(bot, update):
    logger.info('He recibido un comando stats')
    for j in jugadores:
        bot.send_message(
            chat_id=update.message.chat_id,
            text=""+ Jugador.getNombre(j) + " : "
        )
#Comando para dar un numero aleatorio entre 1 y 10
def random10(bot, update):
    num = random.randint(1, 10)
    bot.send_message(
        chat_id = update.message.chat_id,
        text="Este es el número aleatorio entre el 1 y el 10:\t" + str(num)
    )
if __name__ == '__main__':

    updater = Updater(token=BOT_KEY)
    dispatcher = updater.dispatcher
    leerJugadores()

    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('rand', random10))
    updater.start_polling()
    updater.idle()
