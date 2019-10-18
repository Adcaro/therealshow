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

#-------------------------------------------------------------------Variables de entorno-------------------------------------------------------------------------------------
# Getting mode, so we could define run function for local and Heroku setup
MODE = os.environ.get("BOT_MODE")
TOKEN = os.environ.get("BOT_KEY")
FTP_USR = os.environ.get("FTPUSR")
FTP_PASS = os.environ.get("FTPPASS")
#-------------------------------------------------------------------Variables de entorno-------------------------------------------------------------------------------------

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

def darDeAltaPartido(tematica, fecha, hora, lugar, mensaje_Partido, chat, texto):

    partidoET = ET.Element("partido")
    partidoET.set('estado', 'incompleto')

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

    textET = ET.SubElement(partidoET, "texto")
    textET.text = str(texto)

    jugadoresET = ET.SubElement(partidoET, "jugadores")
    jugadoresET.set('numero', '0')

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
    leerstats = ""
    for p in argumentos:
        leerstats = leerstats + p + " "
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
    cursorObj.execute('SELECT nombre, ngoles FROM jugador ORDER BY ngoles DESC, pjugados ASC, pganados DESC LIMIT 7')
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
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para convocar un partido
def convocar(bot, update, args):
    logger.info('He recibido un comando Convocar Partido de {}'.format(update.message.from_user.first_name))
    #Si el usuario es un administrador
    if(update.message.from_user.id == 776132385 or update.message.from_user.id == 164625805):
        logger.info('Usuario valido para generar partido')
        #Si no se pasan argumentos
        if(len(args) == 0):
            bot.send_message(
                reply_to_message_id= update.message.message_id,
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
                    reply_to_message_id= update.message.message_id,
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
                if(incompleto):
                    bot.send_message(
                        reply_to_message_id= update.message.message_id,
                        chat_id=update.message.chat_id,
                        text="@" + str(update.message.from_user.username) + " ya hay una convocatoria activa no puedes crear un partido aun.",
                        parse_mode= ParseMode.MARKDOWN
                    )
                else:
                    #Generar el mensaje
                    texto_Partido = "⚽ `" + partidoItem[0] + "` ⚽"
                    texto_Partido = texto_Partido + "\n\n🗓 *" + partidoItem[1] + "*"
                    texto_Partido = texto_Partido + "\n🕑 [{}]".format(partidoItem[2])
                    texto_Partido = texto_Partido + "\n🏟 _" + partidoItem[3] + "_"
                    texto_Partido = texto_Partido + "\n\n Jugadores: \n"
                    mensaje_Partido = bot.send_message(
                        chat_id=update.message.chat_id,
                        text=texto_Partido,
                        parse_mode= ParseMode.MARKDOWN,
                    )
                    #Guardamos la informacion del partido en la base de datos
                    darDeAltaPartido(partidoItem[0], partidoItem[1], partidoItem[2], partidoItem[3], mensaje_Partido.message_id, update.message.chat_id, texto_Partido)
                    bot.pin_chat_message(chat_id=update.message.chat_id, message_id = mensaje_Partido.message_id, disable_notification=None, timeout=None)
    #Si el usuario no es un administrador
    else:
        bot.send_message(
            reply_to_message_id= update.message.message_id,
            chat_id=update.message.chat_id,
            text="@" + str(update.message.from_user.username) + " solo el Convocator puede convocar",
            parse_mode= ParseMode.MARKDOWN
        )
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para apuntarse a un Partido
def apuntarsePartido(bot, update, args):
    logger.info('He recibido un comando apuntarse')
    #Descargar db
    descargarXML()
    if(len(args) == 0):
        bot.send_message(
            reply_to_message_id= update.message.message_id,
            chat_id=update.message.chat_id,
            text="Para apuntarte al partido tienes que poner, a continuación del comando, un nombre.",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        # Buscar el partido activo
        with open('partidos.xml', 'r', encoding='latin-1') as utf8_file:
            tree = ET.parse('partidos.xml')
            root = tree.getroot()
        partido = root.find('.//partido[@estado="incompleto"]')
        if(partido == None):
            #mensaje de que no hay partido activo
            bot.send_message(
                reply_to_message_id= update.message.message_id,
                chat_id=update.message.chat_id,
                text="No hay ningun partido al que apuntarse, abrid una convocatoria.",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
            aux_jugador = partido.findall(".//jugador")
            esta=False
            for j in aux_jugador:
                if(j.get("nombre") == update.message.from_user.first_name):
                    esta = True
            if(esta):
                #El jugador ya existe y hay que editar el texto
                bot.send_message(
                    reply_to_message_id= update.message.message_id,
                    chat_id=update.message.chat_id,
                    text="Ya estás apuntado",
                    parse_mode= ParseMode.MARKDOWN
                )
            else:
                idmensaje = partido.find("mensaje").text
                idchat = partido.find("chat").text
                textmensaje = partido.find("texto").text
                njugadores = partido.find("jugadores").get("numero")
                if(njugadores == "10"):
                    bot.send_message(
                        reply_to_message_id= update.message.message_id,
                        chat_id=update.message.chat_id,
                        text="La convocatoria está completa. En futuras actualizaciones se te colocará como suplente (aún sin implementar)",
                        parse_mode= ParseMode.MARKDOWN
                    )
                else:
                    #Sacar la tematica del jugador
                    tematicaJugador = ""
                    for p in args:
                        tematicaJugador = tematicaJugador + p + " "
                    #Add jugador
                    for jugador in partido.findall("jugador"):
                        jugador.find("tematica")
                    #Extraer jugadores
                    #Comprobar si un jugador está ya apuntado
                    if(not update.message.from_user.id):
                        bot.send_message(
                            reply_to_message_id= update.message.message_id,
                            chat_id=update.message.chat_id,
                            text="" + update.message.from_user.username + " ya estas apuntado a esta convocatoria.",
                            parse_mode= ParseMode.MARKDOWN
                        )
                    else:
                        try:
                            tematicaJugador2 = textmensaje + "\n {}) ".format(int(njugadores)+1) + tematicaJugador + " - ({})".format(update.message.from_user.first_name)
                            bot.edit_message_text(chat_id=idchat,
                                message_id=idmensaje,
                                text=tematicaJugador2,
                                parse_mode= ParseMode.MARKDOWN)
                            jugadoresET = partido.find("jugadores")
                            n = int(jugadoresET.get('numero'))
                            jugadoresET.set('numero', str(n+1))
                            if(n == 10):
                                partido.set("estado", 'completo')
                            textmensajeET = partido.find("texto")
                            textmensajeET.text = str(tematicaJugador2)
                            player = ET.SubElement(jugadoresET, "jugador")
                            player.set('nombre', update.message.from_user.first_name)
                            player.set('id', str(update.message.from_user.id))
                            player.set('ntematica', tematicaJugador)
                            player.set('goles', '0')
                            player.set('asist', '0')
                            tree.write('partidos.xml')
                            ftp = FTP('ftpupload.net')
                            ftp.login(FTP_USR,FTP_PASS)
                            ftp.cwd('htdocs/trs-db')
                            try:
                                ftp.storbinary('STOR partidos.xml', open('partidos.xml', 'rb'))
                            except:
                                print ("Error")
                            ftp.quit()
                            bot.send_message(
                                reply_to_message_id= update.message.message_id,
                                chat_id=update.message.chat_id,
                                text="Apuntado!😉",
                                parse_mode= ParseMode.MARKDOWN
                            )
                        except:
                            raise
                            bot.send_message(
                                reply_to_message_id= update.message.message_id,
                                chat_id=update.message.chat_id,
                                text="No se ha podido apuntar al partido por un error 😢",
                                parse_mode= ParseMode.MARKDOWN
                            )

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para apuntarse a un Partido
def apuntarBot(bot, update, args):
    logger.info('He recibido un comando apuntar bot')
    #Descargar db
    descargarXML()
    if(len(args) == 0):
        bot.send_message(
            reply_to_message_id= update.message.message_id,
            chat_id=update.message.chat_id,
            text="Para apuntar un bot al partido tienes que poner: nombre jugador y tematica jugador",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        # Buscar el partido activo
        with open('partidos.xml', 'r', encoding='latin-1') as utf8_file:
            tree = ET.parse('partidos.xml')
            root = tree.getroot()
        partido = root.find('.//partido[@estado="incompleto"]')
        if(partido == None):
            #mensaje de que no hay partido activo
            bot.send_message(
                reply_to_message_id= update.message.message_id,
                chat_id=update.message.chat_id,
                text="No hay ningun partido al que apuntar un jugador, abrid una convocatoria.",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
            descargarDB()
            #Abrir conexion sql
            con = sqlite3.connect('therealshow.db')
            #Creamos un cursor
            cursorObj = con.cursor()
            #Consulta para sacar las stats de un jugador
            try:
                cursorObj.execute('SELECT idjugador, nombre FROM jugador WHERE nombre IS "{}"'.format(args[0]))
                existe = cursorObj.fetchall()
            except:
                existe = None
            #Cerrar la conexion SQL
            con.close()
            if(not existe):
                #mensaje de que no hay partido activo
                bot.send_message(
                    reply_to_message_id= update.message.message_id,
                    chat_id=update.message.chat_id,
                    text="No hay ningun bot con ese nombre.",
                    parse_mode= ParseMode.MARKDOWN
                )
            else:
                aux_jugador = partido.findall(".//jugador")
                esta=False
                for j in aux_jugador:
                    if(j.get("nombre") == args[0]):
                        esta = True
                if(esta):
                    #El jugador ya existe y hay que editar el texto
                    bot.send_message(
                        reply_to_message_id= update.message.message_id,
                        chat_id=update.message.chat_id,
                        text="Ese jugador ya está apuntado",
                        parse_mode= ParseMode.MARKDOWN
                    )
                else:
                    idmensaje = partido.find("mensaje").text
                    idchat = partido.find("chat").text
                    textmensaje = partido.find("texto").text
                    njugadores = partido.find("jugadores").get("numero")
                    if(njugadores == "10"):
                        bot.send_message(
                            reply_to_message_id= update.message.message_id,
                            chat_id=update.message.chat_id,
                            text="La convocatoria está completa. En futuras actualizaciones se te colocará como suplente (aún sin implementar)",
                            parse_mode= ParseMode.MARKDOWN
                        )
                    else:
                        #Sacar la tematica del jugador
                        tematicaJugador = ""
                        botjugador = args[0]
                        args.pop(0)
                        for p in args:
                            tematicaJugador = tematicaJugador + p + " "
                        tematicaJugador2 = textmensaje + "\n {}) ".format(int(njugadores)+1) + tematicaJugador + " - ({})".format(botjugador)
                        bot.edit_message_text(chat_id=idchat,
                            message_id=idmensaje,
                            text=tematicaJugador2,
                            parse_mode= ParseMode.MARKDOWN)
                        bot.send_message(
                            reply_to_message_id= update.message.message_id,
                            chat_id=update.message.chat_id,
                            text="{} apuntado!😉".format(botjugador),
                            parse_mode= ParseMode.MARKDOWN
                        )
                        jugadoresET = partido.find("jugadores")
                        n = int(jugadoresET.get('numero'))
                        jugadoresET.set('numero', str(n+1))
                        if(n == 10):
                            partido.set("estado", 'completo')
                        textmensajeET = partido.find("texto")
                        textmensajeET.text = str(tematicaJugador2)
                        player = ET.SubElement(jugadoresET, "jugador")
                        player.set('nombre', botjugador)
                        player.set('id', "None")
                        player.set('ntematica', tematicaJugador)
                        player.set('goles', '0')
                        player.set('asist', '0')
                        tree.write('partidos.xml')
                        ftp = FTP('ftpupload.net')
                        ftp.login(FTP_USR,FTP_PASS)
                        ftp.cwd('htdocs/trs-db')
                        try:
                            ftp.storbinary('STOR partidos.xml', open('partidos.xml', 'rb'))
                        except:
                            print ("Error")
                        ftp.quit()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando para subir stats
def subirStats(bot, update, args):
    logger.info('He recibido un comando para subir stats de {}'.format (update.message.from_user.first_name))
    admins = bot.getChatAdministrators(update.message.chat_id)
    user = bot.getChatMember(update.message.chat_id, update.message.from_user.id, timeout=None)
    if(user in admins and validarStats(args)):
        #Bajar las bases de datos
        descargarXML()
        descargarDB()
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        # Buscar el partido activo
        with open('partidos.xml', 'r', encoding='latin-1') as utf8_file:
            tree = ET.parse('partidos.xml')
            root = tree.getroot()
        partido = root.find('.//partido[@estado="completo"]')
        #Update stats
        i = 0
        while(i<20):
            statsaux = args[i+1].split('-')
            logger.info("Actualizando stats de {} con goles {} asistencias {} ganados {}".format(args[i], statsaux[0], statsaux[1], statsaux[2]))
            cursorObj.execute('SELECT nombre, ngoles, nasistencias, pganados, pjugados, img FROM jugador WHERE nombre IS "{}"'.format(args[i]))
            datosJugador = cursorObj.fetchall()
            if(datosJugador):
                cursorObj.execute('UPDATE jugador SET ngoles = ngoles + {} WHERE nombre IS "{}"'.format(statsaux[0], args[i]))
                cursorObj.execute('UPDATE jugador SET nasistencias = nasistencias + {} WHERE nombre IS "{}"'.format(statsaux[1], args[i]))
                cursorObj.execute('UPDATE jugador SET pganados = pganados + {} WHERE nombre IS "{}"'.format(statsaux[2], args[i]))
                cursorObj.execute('UPDATE jugador SET pjugados = pjugados + 1 WHERE nombre IS "{}"'.format(args[i]))
                if(statsaux[2]):
                    cursorObj.execute('UPDATE jugador SET racha = racha + 1 WHERE nombre IS "{}"'.format(args[i]))
                else:
                    cursorObj.execute('UPDATE jugador SET racha = 0 WHERE nombre IS "{}"'.format(args[i]))
            else:
                bot.send_message(
                    chat_id = update.message.chat_id,
                    text = "Error en la base de datos con el usuario {}".format(args[i]),
                    parse_mode = ParseMode.MARKDOWN
                )
                i=99
            i = i + 2
        if(i < 99):
            #Si todo ha salido bien
            cursorObj.execute('UPDATE season SET partidos = partidos + 1 WHERE id IS 2')
            bot.send_message(
                chat_id = update.message.chat_id,
                text = "Stats actualizados correctamente",
                parse_mode = ParseMode.MARKDOWN
            )
            #Realizar un commit
            con.commit()
            #Cerrar la conexion SQL
            con.close()
            #Subir la base de datos
            subirDB()
        else:
            con.close()
        #Eliminar el mensaje
        bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    else:
        bot.send_message(
            chat_id = update.message.chat_id,
            text = "El formato de la stats no es válido o no tienes permiso para modificar las stats <no se han realizado cambios en la base de datos>",
            parse_mode = ParseMode.MARKDOWN
        )
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Comando de resumen de la season 2
def estadoSeason2(bot, update):
    logger.info('He recibido un comando para conocer el estado de la season 2 en el grupo {}'.format(update.message.chat_id))
    descargarDB()
    #Abrir conexion sql
    con = sqlite3.connect('therealshow.db')
    #Creamos un cursor
    cursorObj = con.cursor()
    #Consulta los partidos jugados
    cursorObj.execute('SELECT partidos, fecha, vcolor, vblanco FROM season WHERE id IS 2')
    partidosjugados = cursorObj.fetchall()
    #Consultar el ganador de goles
    cursorObj.execute('SELECT nombre, ngoles FROM jugador ORDER BY ngoles DESC, pjugados ASC LIMIT 1')
    ganadorGoles = cursorObj.fetchall()
    #Consultar el ganador de asistencias
    cursorObj.execute('SELECT nombre, nasistencias FROM jugador ORDER BY nasistencias DESC, pjugados ASC, pganados DESC LIMIT 1')
    asistencias = cursorObj.fetchall()
    #Consultar el ganador de racha
    cursorObj.execute('SELECT nombre, racha FROM jugador ORDER BY racha DESC, pjugados ASC, pganados DESC LIMIT 1')
    racha = cursorObj.fetchall()
    #Consultar el mejor indice de vicotrias
    cursorObj.execute('SELECT nombre, pganados, pjugados FROM jugador ORDER BY pganados DESC, pjugados ASC LIMIT 1')
    indice = cursorObj.fetchall()
    #Mandamos el mensaje resumen
    bot.send_message(
            chat_id = update.message.chat_id,
            text = "\t📒*Estado season 2*📒\n\n📅Fecha de inicio: {}\n⚽️Partidos totales: {}\n🏆PseudoGanador Goles: {}\n🏆PseudoGanador Asistencias: {} \n📈Mejor indice victorias: {} ({}/{})\n📿Zamuleto: {} ({})\n⚪️Victorias Blancos: {}\n🔵Victorias Color: {}".format(partidosjugados[0][1],partidosjugados[0][0], ganadorGoles[0][0], asistencias[0][0], indice[0][0], indice[0][1], indice[0][2], racha[0][0], racha[0][1], partidosjugados[0][3], partidosjugados[0][2]),
            parse_mode = ParseMode.MARKDOWN
        )
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------Funcion principal--------------------------------------------------------------------------------------------------
#Main Function
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('mystats', myStats))
    dispatcher.add_handler(CommandHandler('subirstats', subirStats, pass_args=True))
    dispatcher.add_handler(CommandHandler('season2', estadoSeason2))
    dispatcher.add_handler(CommandHandler('convocar', convocar, pass_args=True))
    dispatcher.add_handler(CommandHandler('apuntarse', apuntarsePartido, pass_args=True))
    dispatcher.add_handler(CommandHandler('apuntarbot', apuntarBot, pass_args=True))
    run(updater)