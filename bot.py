
# This file contains the source code of The Real Show Telegram Bot.
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
import xml.etree.ElementTree as ET
import random
import logging
import os
import sys
import sqlite3

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

#-------------------------------------------------------------------CHANGE---------------------------------------------------------------------------------------------------
# Getting mode, so we could define run function for local and Heroku setup
mode = os.environ.get("BOT_MODE")
TOKEN = os.environ.get("BOT_KEY")
#-------------------------------------------------------------------CHANGE---------------------------------------------------------------------------------------------------

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
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando de inicio del Bot
def start(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Bienvenido al Bot de The Real Show FC. Consulta estadísticas y apúntate a nuestros partidos.",
        parse_mode= ParseMode.MARKDOWN
    )

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para mostrar las stats
def stats(bot, update):
    logger.info('He recibido un comando stats')
    #Abrir conexion sql
    con = sqlite3.connect('therealshow.db')
    #Creamos un cursor
    cursorObj = con.cursor()
    #Consulta para sacar los jugadores ordenados por goles
    cursorObj.execute('SELECT nombre, ngoles FROM jugador ORDER BY ngoles DESC, pjugados ASC LIMIT 7')
    #Samos todas las columnas de la consulta
    datosGolesJugadores = cursorObj.fetchall()
    #Preparar el mensaje
    textStat = "*🏆TOP Golos The Real Show Season 2🏆*\n\n"
    for j in datosGolesJugadores:
        textStat = textStat + j[0] + "\t ---> " + str(j[1]) + "\n"
    bot.send_message(
        chat_id=update.message.chat_id,
        text=textStat,
        parse_mode= ParseMode.MARKDOWN
    )
    #Consulta para sacar los jugadores ordenados por asistencias
    cursorObj.execute('SELECT nombre, nasistencias FROM jugador ORDER BY nasistencias DESC, pjugados ASC LIMIT 7')
    #Samos todas las columnas de la consulta
    datosAsistJugadores = cursorObj.fetchall()
    #Preparar el mensaje
    textStat = "*🏅TOP Asistencias The Real Show Season 2🏅*\n\n"
    for j in datosAsistJugadores:
        textStat = textStat + j[0] + "\t ---> " + str(j[1]) + "\n"
    bot.send_message(
        chat_id=update.message.chat_id,
        text=textStat,
        parse_mode= ParseMode.MARKDOWN
    )
    #Cerrar la conexion SQL
    con.close()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para mostrar informacion especifica sobre un jugador
def myStats(bot, update):
    logger.info('He recibido un comando MyStats de {}'.format (update.message.from_user.first_name))
    #Abrir conexion sql
    con = sqlite3.connect('therealshow.db')
    #Creamos un cursor
    cursorObj = con.cursor()
    #Consulta para sacar las stats de un jugador
    cursorObj.execute('SELECT nombre, ngoles, nasistencias, pganados, pjugados, img FROM jugador WHERE idtelegram IS {}'.format(update.message.from_user.id))
    #Samos todas las columnas de la consulta
    datosmyStatsJugadores = cursorObj.fetchall()
    #Cerrar la conexion SQL
    con.close()
    #Si la consulta no reporta ningun valor
    if( not datosmyStatsJugadores):
        bot.send_message(
                chat_id=update.message.chat_id,
                text="❌Error: No tienes datos sobre tus estadísticas.❌ \n En breve te darán de alta \n {} ID: \t {}".format(update.message.from_user.first_name, update.message.from_user.id),
                parse_mode= ParseMode.MARKDOWN
            )
    #Si consulta es correcta
    else:
        j = datosmyStatsJugadores[0]
        senderText = "📊 Stats de {} Season 2 📊\n".format(j[0])
        bot.send_photo(chat_id=update.message.chat_id, photo=open(j[5], 'rb'), caption =senderText + "\n\t🥇 Goles : " + str(j[1]) + "\n\t🥈 Asist: " + str(j[2]) + "\n\t🥉 P. Ganados: " + str(j[3]) + "\n\t🥺 P. Perdidos: " + str(j[4]-j[3]) + "\n\t⚽ P. Jugados: " + str(j[4]))

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para iniciar un partido
def crearPartido(bot, update, args):
    logger.info('He recibido un comando CrearPartido de {}'.format (update.message.from_user.first_name))
    #Extraer la lista de admins del grupo
    admins = bot.get_chat_administrators(update.message.chat_id, timeout=None)
    #Determinar el usuario
    user = bot.getChatMember(update.message.chat_id, update.message.from_user.id, timeout=None)
    #Si el usuario es un administrador
    if(user in admins):
        logger.info('Usuario valido para generar partido')
        #Si no se pasan argumentos
        if(len(args) == 0):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="La creación de un partido requiere una temática.",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
        #Si todo esta correcto
            tematica = ""
            for p in args:
                tematica = tematica + p + " "
            #Damos de alta el partido en la base de datos
            #Abrir conexion sql
            con = sqlite3.connect('therealshow.db')
            #Creamos un cursor
            cursorObj = con.cursor()
            #Generar el mensaje
            texto_Partido = "⚽ *" + tematica + "* ⚽"
            mensaje_Partido = bot.send_message(
                chat_id=update.message.chat_id,
                text=texto_Partido,
                parse_mode= ParseMode.MARKDOWN,
            )
            #Recopilamos la informacion del partido
            valoresPartido = (tematica, update.message.chat_id, mensaje_Partido.message_id, update.message.from_user.id, True)
            #Realizamos la insercción en la tabla
            cursorObj.execute('INSERT INTO partido(tematica, idchat, idmensaje, creador, activo) VALUES(?, ?, ?, ?, ?)', valoresPartido)
            #Completamos la modificacion
            con.commit()
            #Cerrar conexion
            con.close()
            bot.pin_chat_message(chat_id=update.message.chat_id, message_id = mensaje_Partido.message_id, disable_notification=None, timeout=None)
    #Si el usuario no es un administrador
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="@" + str(update.message.from_user.username) + " no tienes permiso para crear una Convocatoria de Partido.",
            parse_mode= ParseMode.MARKDOWN
        )
#Comando para apuntarse a un Partido
def apuntarsePartido(bot, update, args):
    if(len(args) == 0):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Para apuntarte al partido tienes que poner en el mensaje un nombre.",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        #Debemos sacar el partido activo
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        #Consulta para sacar las stats de un jugador
        cursorObj.execute('SELECT tematica, idchat, idmensaje, creador, activo FROM partido WHERE activo IS 1 AND idchat IS {}'.format(update.message.chat_id))
        #Samos todas las columnas de la consulta
        datosPartido = cursorObj.fetchall()
        #Cerrar la conexion SQL
        con.close()
        if(not datosPartido):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="" + update.message.from_user.username + " no hay partidos activos, si eres admin puedes convocar uno.",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
            #Sacar la tematica del jugador
            tematicaJugador = ""
            for p in args:
                tematicaJugador = tematicaJugador + p + " "
            #Add participante a partido
            #Extraer mensaje por id
            mensajeConvocatoria = update.message(chat_id = chat_id=datosPartido[0][1],
            message_id=datosPartido[0][2])
            
            update.message.from_user.username
            bot.edit_message_text(chat_id=datosPartido[0][1],
                      message_id=datosPartido[0][2],
                      text=
                      parse_mode= ParseMode.MARKDOWN)
            edit_text( text=partido.texto, parse_mode= ParseMode.MARKDOWN)
            partido.participantes[update.message.from_user.username] = tematicaJugador
            partido.texto = partido.texto + "\n - " + tematicaJugador + "\t @" + update.message.from_user.username
            partido.mensaje.edit_text( text=partido.texto, parse_mode= ParseMode.MARKDOWN)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Para ver cuan gay estas hoy
def gay(bot, update):
    num = random.randint(0, 100)
    bot.send_message(
        chat_id = update.message.chat_id,
        text="Este es el número aleatorio entre el 1 y el 10:\t" + str(num)
    )
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Para ver cuan gay estas hoy
def showid(bot, update):
    print("{} ID: \t {}".format(update.message.from_user.first_name, update.message.from_user.id))
    bot.send_message(
        chat_id = update.message.chat_id,
        text="Gracias {}".format(update.message.from_user.first_name)
    )
#Main Function
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    leerJugadores()

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('mystats', myStats))
    dispatcher.add_handler(CommandHandler('id', showid))
    dispatcher.add_handler(CommandHandler('crearpartido', crearPartido, pass_args=True))
    dispatcher.add_handler(CommandHandler('apuntarse', apuntarsePartido, pass_args=True))

    run(updater)
