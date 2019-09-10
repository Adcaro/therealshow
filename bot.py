
# This file contains the source code of The Real Show Telegram Bot.
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
import xml.etree.ElementTree as ET
import random
import logging
import os
import sys
import sqlite3

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('TheRealShow')

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
    #Determinar el usuario
    user = bot.getChatMember(update.message.chat_id, update.message.from_user.id, timeout=None)
    #Si el usuario es un administrador
    if(user):
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
            valoresPartido = (tematica, update.message.chat_id, mensaje_Partido.message_id)
            #Realizamos la insercción en la tabla
            cursorObj.execute('INSERT INTO partido(tematica, idchat, idmensaje) VALUES(?, ?, ?)', valoresPartido)
            #Completamos la modificacion
            con.commit()
            #Cerrar conexion
            con.close()
            bot.pin_chat_message(chat_id=update.message.chat_id, message_id = mensaje_Partido.message_id, disable_notification=None, timeout=None)
    #Si el usuario no es un administrador
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="@" + str(update.message.from_user.username) + " solo el Convocator puede convocar sucio humano.",
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
            text="PACHRICOLAJE 🔨\n",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="" + update.message.from_user.username + " no eres el Haceedor de Equipos, no toques.",
            parse_mode= ParseMode.MARKDOWN
        )
#Main Function
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('mystats', myStats))
#------------------------------------------------DEV--------------------------------------------------------------------------------------------------
    dispatcher.add_handler(CommandHandler('crearpartido', crearPartido, pass_args=True))
    dispatcher.add_handler(CommandHandler('apuntarse', apuntarsePartido, pass_args=True))
    dispatcher.add_handler(CommandHandler('equipos', crearEquipos))

    run(updater)
