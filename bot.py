
# This file contains the source code of The Real Show Telegram Bot.
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
import xml.etree.ElementTree as ET
import random
import logging
import os
import sys

#Clase partido
class Partido(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.tematica = ""
        self.participantes = dict()
        self.fecha = ""
        self.lugar = ""
        self.idMensaje = ""
        self.texto = ""
        self.activo = False
#clase de jugador
class Jugador(object):
    '''
    classdocs
    '''
    def __init__(self, n, g, a, ga, pe, ni):
        '''
        Constructor
        '''
        self.nombre = n
        self.goles = g
        self.asistencias = a
        self.ganados = ga
        self.perdidos = pe
        self.nick = ni
#
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('TheRealShow')
partido = Partido()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.environ.get("BOT_MODE")
TOKEN = os.environ.get("BOT_KEY")

if mode == "dev":
    def run(updater):
        updater.start_polling()
        updater.idle()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "5000"))
        HEROKU_APP_NAME = os.environ.get("therealshow")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://therealshow.herokuapp.com/" + TOKEN)
        updater.idle()
else:
    logger.error("No MODE specified!")
    sys.exit(1)

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
            '''
            Pendiente de modificar
            jugador = Jugador(nombre, goles, asistencias, ganados, perdidos)
            jugadores[nombre] = jugador
            '''

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
#-----------------------------------------------------------------
#Comando de inicio del Bot
def start(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Iniciando Bot, leyendo datos...",
        parse_mode=telegram.ParseMode.MARKDOWN
    )
#Comando para mostrar las stats
def stats(bot, update):
    logger.info('He recibido un comando stats')
    with open('stats.xml', 'r', encoding='latin-1') as utf8_file:
        tree = ET.parse(utf8_file)
    root = tree.getroot()
    jugadores = root.findall('jugador')
    textStat = "*Stats The Real Show PreSeason*\n"
    for j in jugadores:
        textStat = textStat + j[0].text + "\n Goles : " + j[1].text + "\t Asist: " + j[2].text + "\n"
    bot.send_message(
        chat_id=update.message.chat_id,
        text=textStat,
        parse_mode= ParseMode.MARKDOWN
    )
#Comando para dar un numero aleatorio entre 1 y 10
def random10(bot, update):
    num = random.randint(1, 10)
    bot.send_message(
        chat_id = update.message.chat_id,
        text="Este es el número aleatorio entre el 1 y el 10:\t" + str(num)
    )
#Comando para mostrar informacion especifica sobre un jugador
def myStats(bot, update):
    logger.info('He recibido un comando MyStats de {}'.format (update.message.from_user.first_name))
    with open('stats.xml', 'r', encoding='latin-1') as utf8_file:
        tree = ET.parse(utf8_file)
    root = tree.getroot()
    jugadores = root.findall('jugador')
    for j in jugadores:
        if(j[5].text == update.message.from_user.first_name):
            bot.send_message(
                chat_id=update.message.chat_id,
                text=j[0].text + "\n Goles : " + j[1].text + "\t Asist: " + j[2].text + "\t P. Ganados: " +j[3].text + "\t P. Perdidos: " + j[4].text + "\n",
                parse_mode= ParseMode.MARKDOWN
            )
            bot.send_photo(chat_id=update.message.chat_id, photo=open(j[6].text, 'rb'))
            break
#Comando para iniciar un partido
def crearPartido(bot, update, args):
    logger.info('He recibido un comando CrearPartido de {}'.format (update.message.from_user.first_name))
    admins = bot.get_chat_administrators(update.message.chat_id, timeout=None)
    user = bot.getChatMember(update.message.chat_id, update.message.from_user.id, timeout=None)
    if(user in admins):
        logger.info('Usuario valido para generar partido')
        if(len(args) == 0):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="La creación de un partido requiere una temática.",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
            tematica = ""
            for p in args:
                tematica = tematica + p + " "
            partido.tematica = tematica
            partido.texto = "⚽ " + "*" + tematica + "*" + "⚽"
            mensaje_Partido = bot.send_message(
                chat_id=update.message.chat_id,
                text=partido.texto,
                parse_mode= ParseMode.MARKDOWN,
            )
            partido.mensaje = mensaje_Partido
            partido.idMensaje = mensaje_Partido.message_id
            bot.pin_chat_message(chat_id=update.message.chat_id, message_id = partido.idMensaje, disable_notification=None, timeout=None)
        #pinned_message
        #bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
        #
        #'''bot.edit_text(chat_id=message.chat_id,
        #                 message_id=message.message_id)'''
        #
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="@" + update.message.from_user.username + " no tienes permiso para crear una Convocatoria de Partido.",
            parse_mode= ParseMode.MARKDOWN
        )
#Comando para apuntarse a un Partido
def apuntarsePartido(bot, update, args):
    tematicaJugador = ""
    for p in args:
        tematicaJugador = tematicaJugador + p + " "
    if (tematicaJugador in partido.participantes.values()):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="@" + update.message.from_user.username + " ya existe un nombre identico para esta temática.",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        partido.participantes[update.message.from_user.username] = tematicaJugador
        partido.texto = partido.texto + "\n - " + tematicaJugador + "\t @" + update.message.from_user.username
        partido.mensaje.edit_text( text=partido.texto, parse_mode= ParseMode.MARKDOWN)
#Main Function
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    leerJugadores()

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('rand', random10))
    dispatcher.add_handler(CommandHandler('mystats', myStats))
    dispatcher.add_handler(CommandHandler('crearpartido', crearPartido, pass_args=True))
    dispatcher.add_handler(CommandHandler('apuntarse', apuntarsePartido, pass_args=True))

    run(updater)
