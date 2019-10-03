# This file contains the source code of The Real Show Telegram Bot.
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
from ftplib import FTP
import xml.etree.ElementTree as ET
import random
import logging
import os
import sys
import sqlite3
import re


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('TheRealShow')

#-------------------------------------------------------------------CHANGE---------------------------------------------------------------------------------------------------
# Getting mode, so we could define run function for local and Heroku setup
MODE = os.environ.get("BOT_MODE")
TOKEN = os.environ.get("BOT_KEY")
FTP_USR = os.environ.get("FTPUSR")
FTP_PASS = os.environ.get("FTPPASS")
#-------------------------------------------------------------------CHANGE---------------------------------------------------------------------------------------------------

if MODE == "dev":
    def run(updater):
        updater.start_polling()
        updater.idle()
elif MODE == "prod":
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

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------Funciones auxiliares-----------------------------------------------------------------------------------------------
def descargarDB():
    #Bajar la db
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-db')
    try:
        ftp.retrbinary("RETR therealshow.db" ,open('therealshow.db', 'wb').write)
    except:
        print ("Error conect ftp server")
    ftp.quit()

def subirDB():
    #Subir la db
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-db')
    try:
        ftp.storbinary('STOR therealshow.db', open('therealshow.db', 'rb'))
    except:
        print ("Error conect ftp server")
    ftp.quit()

def descargarXML():
    #Bajar la db
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-db')
    try:
        ftp.retrbinary("RETR partidos.xml" ,open('partidos.xml', 'wb').write)
    except:
        print ("Error conect ftp server")
    ftp.quit()

def descargarFicha(imagen):
    #Descargar imagen
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-fichas')
    try:
        ftp.retrbinary("RETR " + imagen ,open(imagen, 'wb').write)
    except:
        print ("Error conect ftp server")
    ftp.quit()

def darDeAltaPartido(tematica, fecha, hora, lugar, mensaje_Partido, chat):

    partidoET = ET.Element("partido")
    partidoET.set('Estado', 'incompleto')

    tematicaET = ET.SubElement(partidoET, "tematica")
    tematicaET.text = str(tematica)

    fechaET = ET.SubElement(partidoET, "fecha")
    fechaET.text = str(fecha)

    horaET = ET.SubElement(partidoET, "hora")
    horaET.text = str(hora)

    lugarET = ET.SubElement(partidoET, "lugar")
    lugarET.text = str(lugar)

    mensajeET = ET.SubElement(partidoET, "mensaje")
    mensajeET.text = str(mensaje_Partido)

    chatET = ET.SubElement(partidoET, "chat")
    chatET.text = str(chat)

    jugadoresET = ET.SubElement(partidoET, "jugadores")
    jugadoresET.set('numero', "0")

    # Escribir el fichero
    with open('partidos.xml', 'r', encoding='latin-1') as utf8_file:
        tree = ET.parse('partidos.xml')
        root = tree.getroot()
        root.insert(0, partidoET)
        tree.write('partidos.xml')
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-db')
    try:
        ftp.storbinary('STOR partidos.xml', open('partidos.xml', 'rb'))
    except:
        print ("Error")
    ftp.quit()

def validarStats(argumentos):
    print(argumentos)
    leerstats = ""
    for p in argumentos:
        leerstats = leerstats + p + " "
    print(leerstats)
    match = re.search("([A-z]+[ ][0-9]+[-][0-9]+[-][01][ ]){10}", leerstats)
    if(match):
        return True
    else:
        return False



#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para mostrar las stats
def stats(bot, update):
    logger.info('He recibido un comando stats')
    descargarDB()
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
    cursorObj.execute('SELECT nombre, nasistencias FROM jugador ORDER BY nasistencias DESC, pjugados ASC, pganados DESC LIMIT 7')
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
    descargarDB()
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
        #Sacar el jugador
        j = datosmyStatsJugadores[0]
        descargarFicha(j[5])
        #Mostrar mensaje
        senderText = "📊 Stats de {} Season 2 📊\n".format(j[0])
        bot.send_photo(chat_id=update.message.chat_id, photo=open(j[5], 'rb'), caption =senderText + "\n\t🥇 Goles : " + str(j[1]) + "\n\t🥈 Asist: " + str(j[2]) + "\n\t🥉 P. Ganados: " + str(j[3]) + "\n\t🥺 P. Perdidos: " + str(j[4]-j[3]) + "\n\t⚽ P. Jugados: " + str(j[4]))
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para convocar un partido
def convocar(bot, update, args):
    logger.info('He recibido un comando CrearPartido de {}'.format(update.message.from_user.first_name))
    #Si el usuario es un administrador
    if(update.message.from_user.id == 776132385 or update.message.from_user.id == 164625805):
        logger.info('Usuario valido para generar partido')
        #Si no se pasan argumentos
        if(len(args) == 0):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="La creación de un partido requiere una temática, fecha, hora, lugar, sepearados por -",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
        #Si todo esta correcto
            #Leer los parametros
            parametros = ""
            for p in args:
                parametros = parametros + p + " "
            #Damos de alta el partido en la base de datos
            partidoItem = parametros.split("-")
            if(len(partidoItem) != 4):
                bot.send_message(
                chat_id=update.message.chat_id,
                text="La creación de un partido requiere una temática, fecha, hora, lugar, sepearados por -",
                parse_mode= ParseMode.MARKDOWN
                )
            else:
                #Descargar xml
                descargarXML()
                #Parsear xml
                with open('partidos.xml', 'r', encoding='latin-1') as utf8_file:
                    tree = ET.parse(utf8_file)
                root = tree.getroot()
                incompleto = root.find('./partido[@Estado="incompleto"]')
                completo = root.find('./partido[@Estado="completo"]')
                if(incompleto):
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="@" + str(update.message.from_user.username) + " ya hay una convocatoria activa no puedes crear un partido aun.",
                        parse_mode= ParseMode.MARKDOWN
                    )
                elif(completo):
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="@" + str(update.message.from_user.username) + " existe un partido ya completo, espera a que se juege para crear uno.",
                        parse_mode= ParseMode.MARKDOWN
                    )
                else:
                    #Generar el mensaje
                    texto_Partido = "⚽ *" + partidoItem[0] + "* ⚽"
                    texto_Partido = texto_Partido + "\n\n🗓 " + partidoItem[1]
                    texto_Partido = texto_Partido + "\n🕑" + partidoItem[2]
                    texto_Partido = texto_Partido + "\n🏟 " + partidoItem[3]
                    texto_Partido = texto_Partido + "\n\n Jugadores: \n"
                    mensaje_Partido = bot.send_message(
                        chat_id=update.message.chat_id,
                        text=texto_Partido,
                        parse_mode= ParseMode.MARKDOWN,
                    )
                    #Guardamos la informacion del partido en la base de datos
                    darDeAltaPartido(partidoItem[0], partidoItem[1], partidoItem[2], partidoItem[3], mensaje_Partido.message_id, update.message.chat_id)
                    bot.pin_chat_message(chat_id=update.message.chat_id, message_id = mensaje_Partido.message_id, disable_notification=None, timeout=None)
    #Si el usuario no es un administrador
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="@" + str(update.message.from_user.username) + " solo el Convocator puede convocar, sucio plebe",
            parse_mode= ParseMode.MARKDOWN
        )
#Comando para apuntarse a un Partido
def apuntarsePartido(bot, update, args):
    if(len(args) == 0):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Para apuntarte al partido tienes que poner, a continuación del comando, un nombre.",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        #Debemos sacar el partido activo
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        #Consulta para sacar las stats de un jugador
        cursorObj.execute('SELECT tematica, idchat, idmensaje FROM partido WHERE idchat IS {}'.format(update.message.chat_id))
        #Samos todas las columnas de la consulta
        datosPartido = cursorObj.fetchall()
        #Cerrar la conexion SQL
        con.close()
        if(not datosPartido):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="" + update.message.from_user.username + " no hay partidos activos, si eres el Convocador puedes convocar uno.",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
            #Sacar la tematica del jugador
            tematicaJugador = ""
            for p in args:
                tematicaJugador = tematicaJugador + p + " "
            #Add jugador
            #Abrir conexion sql
            con = sqlite3.connect('therealshow.db')
            #Creamos un cursor
            cursorObj = con.cursor()
            #Consulta para sacar las stats de un jugador
            cursorObj.execute('SELECT jugadores, tematicas, idmensaje, id FROM partido WHERE idchat IS {}'.format(update.message.chat_id))
            #Samos todas las columnas de la consulta
            sacarJugadores = cursorObj.fetchall()
            #Cerrar la conexion SQL
            con.close()
            #Extraer jugadores
            sacarJugadores = sacarJugadores [0]
            idJugadores = sacarJugadores [0]
            nombreJugadores = sacarJugadores[1]
            idMensajeAnclado = sacarJugadores[2]
            listaIdJugadores = list(idJugadores.split("~"))
            nombreTematica = ""
            for p in args:
                nombreTematica = nombreTematica + p + " "
            if(update.message.from_user.id in listaIdJugadores):
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="" + update.message.from_user.username + " ya estas apuntado a esta convocatoria.",
                    parse_mode= ParseMode.MARKDOWN
                )
            else:
                nombreJugadores = nombreJugadores + "~" + nombreTematica
                idJugadores = idJugadores + "~" + str(update.message.from_user.id)
                bot.edit_message_text(chat_id=update.message.chat_id,
                    message_id=idMensajeAnclado,
                    text=update.message.text + "\n -" + nombreTematica,
                    parse_mode= ParseMode.MARKDOWN)
                #Abrir conexion sql
                con = sqlite3.connect('therealshow.db')
                #Creamos un cursor
                cursorObj = con.cursor()
                #Usamos el id del partido
                sacarJugadores
                #Consulta para sacar las stats de un jugador
                cursorObj.execute('UPDATE partido SET jugadores = {} WHERE id IS {}'.format(update.message.chat_id, sacarJugadores[3]))
                #Hacer un commit
                con.commit()
                #Cerrar la conexion SQL
                con.close()
#Comando para generar los equipos
def crearEquipos(bot, update):
    if(update.message.from_user.id == 892752079):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="" + update.message.from_user.first_name + " no eres el Haceedor de Equipos, no toques.",
            parse_mode= ParseMode.MARKDOWN
        )
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para subir stats
def subirStats(bot, update, args):
    logger.info('He recibido un comando para subir stats de {}'.format (update.message.from_user.first_name))
    admins = bot.getChatAdministrators(update.message.chat_id)
    user = bot.getChatMember(update.message.chat_id, update.message.from_user.id, timeout=None)
    if(user in admins and validarStats(args)):
        #Numero de argumentos correcto
        descargarDB()
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        #Update stats
        i = 0
        while(i<20):
            statsaux = args[i+1].split('-')
            cursorObj.execute('UPDATE jugador SET ngoles = ngoles + {} WHERE nombre IS "{}"'.format(statsaux[0], args[i]))
            cursorObj.execute('UPDATE jugador SET nasistencias = nasistencias + {} WHERE nombre IS "{}"'.format(statsaux[1], args[i]))
            cursorObj.execute('UPDATE jugador SET pganados = pganados + {} WHERE nombre IS "{}"'.format(statsaux[2], args[i]))
            cursorObj.execute('UPDATE jugador SET pjugados = pjugados + 1 WHERE nombre IS "{}"'.format(args[i]))
            i = i + 2
        #Grabamos los datos
        con.commit()
        #Cerrar la conexion SQL
        con.close()
        #Subir la base de datos
        subirDB()
    else:
        bot.send_message(
            chat_id = update.message.chat_id,
            text = "El formato de la stats no es válido o no tienes permiso para modificar las stats <no se han realizado cambios en la base de datos>",
            parse_mode = ParseMode.MARKDOWN
        )
#Main Function
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('mystats', myStats))
    dispatcher.add_handler(CommandHandler('subirstats', subirStats, pass_args=True))
    run(updater)
