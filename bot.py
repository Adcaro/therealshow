# -*- coding: utf-8 -*-
# This file contains the source code of The Real Show Telegram Bot.
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ftplib import FTP
import xml.etree.ElementTree as ET
import random
import logging
import os
import sys
import sqlite3
from sqlite3 import Error
import re
#Para graficas
import matplotlib
import matplotlib.pyplot as plt


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('TheRealShow')

#-------------------------------------------------------------------Variables de entorno-------------------------------------------------------------------------------------
# Getting mode, so we could define run function for local and Heroku setup
MODE = os.environ.get("BOT_MODE")
TOKEN = os.environ.get("BOT_KEY")
FTP_USR = os.environ.get("FTPUSR")
FTP_PASS = os.environ.get("FTPPASS")
#-------------------------------------------------------------------Definicion de modo----------------------------------------------------------------------------
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
##*/DEBUG
#-------------------------------------------------------------------Variables Globales----------------------------------------------------------------------------
wellcomeText = "Bienvenido al Bot de The Real Show FC. Aun no tienes ficha, escribe /alta un espacio y tu nombre: \nEj: /alta Urri"
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------Funciones Auxiliares-----------------------------------------------------------------------------------------------
#Comprueba si un usuario esta registrado o no en el sistema
def isRegister(telegramID):
    logger.info("Lets check resgisted user {}".format(telegramID))
    downloadDB()
    try:
        #Abrir conexion sql
        connection = sqlite3.connect('therealshow.db')
        logger.info("Connection is established: Databas is current in memory")
    except Error:
        logger.error("Error: Can't connect with the DB - " +  Error)
        sys.exit(0)
    #Consultamos si existe el usuario
    cursorObj = connection.cursor()
    #Consulta si existe un user con ese id
    #request
    cursorObj.execute('SELECT idtelegram FROM jugador WHERE idtelegram IS {}'.format(telegramID))
    rows = cursorObj.fetchall()
    connection.close()
    logger.info("Connection close")
    if (not rows):
        return 0
    return 1

#Descarga la base de datos
def downloadDB():
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-db')
    try:
        ftp.retrbinary("RETR therealshow.db" ,open('therealshow.db', 'wb').write)
    except:
        logger.error("Error: Couldn't connect to ftp server")
    ftp.quit()

#Subir la base de datos al servidor (solo en escrituras)
def uploadDB():
    #Subir la db
    return 0
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-db')
    try:
        ftp.storbinary('STOR therealshow.db', open('therealshow.db', 'rb'))
    except:
        logger.error("Error: Couldn't connect to ftp server")
    ftp.quit()

#Descargar ficha
def downloadCard(imagen):
    #Descargar imagen
    ftp = FTP('ftpupload.net')
    ftp.login(FTP_USR,FTP_PASS)
    ftp.cwd('htdocs/trs-fichas')
    try:
        ftp.retrbinary("RETR " + imagen ,open(imagen, 'wb').write)
    except:
        print ("Error conect ftp server")
    ftp.quit()
#Validar las stats subidas al servidor
def validarStats(argumentos):
    leerstats = ""
    for p in argumentos:
        leerstats = leerstats + p + " "
    match = re.search("([A-z]+[ ][0-9]+[-][0-9]+[-][01][ ]){10}", leerstats)
    if(match):
        return True
    else:
        return False
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------Comandos-----------------------------------------------------------------------------------

#Comando para darse de alta
#RW
def alta(bot, update, args):
    if(isRegister(update.message.from_user.id)):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Ya estás registrado en el sistema.",
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        if(not args):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Debes poner el comando, un espacio y tu nombre:\n/alta Urri",
                parse_mode= ParseMode.MARKDOWN
            )
        else:
            name = ""
            for p in args:
                name = name + p
            #Accedemos a la base de datos para comprobar el nombre
            #Abrir conexion sql
            con = sqlite3.connect('therealshow.db')
            #Creamos un cursor
            cursorObj = con.cursor()
            #Consulta para sacar los jugadores ordenados por goles
            cursorObj.execute('SELECT nombre FROM jugador WHERE UPPER(nombre) IS UPPER("{}")'.format(p))
            #Samos todas las columnas de la consulta
            datos = cursorObj.fetchall()
            if(datos):
                logger.info('Habia una entrada para {} procedo a actualizar su id de telegram.'.format(name))
                #Miramos si ya tenia un id
                cursorObj.execute('SELECT idtelegram FROM jugador WHERE nombre IS "{}"'.format(p))
                idtelegram = cursorObj.fetchall()
                if(idtelegram[0][0] != None):
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="Lo siento estás intentando modificar un usuario de no eres tu, coloca tu nombre.",
                        parse_mode= ParseMode.MARKDOWN
                    )
                else:
                    cursorObj.execute('UPDATE jugador SET idtelegram = {} WHERE UPPER(nombre) IS UPPER("{}")'.format(update.message.from_user.id, name))
                    #Realizar un commit
                    con.commit()
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="✅ Transacción realizada con éxito. Bienvenido a The Real Show FC para consultar tus ficha o tus stats escribe /ficha o /stats",
                        parse_mode= ParseMode.MARKDOWN
                    )
                    
            else:
                logger.info('Los datos de {} no estaban en la base de datos, se creará una nueva tabla'.format(name))
                #Insertamos una entrada para ese usuario:
                cursorObj.execute("INSERT INTO jugador(idtelegram, nombre) VALUES('{}', '{}')".format(update.message.from_user.id, name))
                con.commit()
            con.close()
            uploadDB()
#Comando para mostrar las stats
#R
def stats(bot, update):
    logger.info('He recibido un comando stats de {}'.format(update.message.from_user.first_name))
    #Comprobar si esta registrado
    #Si no esta registrado
    if(not isRegister(update.message.from_user.id)):
        bot.send_message(
            chat_id=update.message.chat_id,
            text=wellcomeText,
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        #Consulta para sacar los jugadores ordenados por goles
        cursorObj.execute('SELECT nombre, ngoles, idtelegram FROM jugador ORDER BY ngoles DESC, pjugados ASC, pganados DESC')
        #Samos todas las columnas de la consulta
        datosGolesJugadores = cursorObj.fetchall()
        #Preparar el mensaje
        textStat = "*🏆TOP Golos The Real Show Season 2🏆*\n\n"
        contador = 1
        presente = False
        for j in datosGolesJugadores:
            if (contador <= 7):
                textStat = textStat + str(contador) + "º - " + j[0] + "\t ---> " + str(j[1]) + "\n"
                contador = contador + 1
                if (j[2] == update.message.from_user.id):
                    presente = True
            elif (not presente):
                contador = contador +1
                if (j[2] == update.message.from_user.id):
                    textStat = textStat + "     ·\n     ·\n"
                    textStat = textStat + str(contador) + "º - " + j[0] + "\t ---> " + str(j[1]) + "\n"
        bot.send_message(
            chat_id=update.message.chat_id,
            text=textStat,
            parse_mode= ParseMode.MARKDOWN
        )
        #Consulta para sacar los jugadores ordenados por asistencias
        cursorObj.execute('SELECT nombre, nasistencias, idtelegram FROM jugador ORDER BY nasistencias DESC, pjugados ASC, pganados DESC')
        #Samos todas las columnas de la consulta
        datosAsistJugadores = cursorObj.fetchall()
        #Preparar el mensaje
        textStat = "*🏅TOP Asistencias The Real Show Season 2🏅*\n\n"
        contador = 1
        presente = False
        for j in datosAsistJugadores:
            if (contador <= 7):
                textStat = textStat + str(contador) + "º - " + j[0] + "\t ---> " + str(j[1]) + "\n"
                contador = contador + 1
                if (j[2] == update.message.from_user.id):
                    presente = True
            elif (not presente):
                contador = contador +1
                if (j[2] == update.message.from_user.id):
                    textStat = textStat + "     ·\n     ·\n"
                    textStat = textStat + str(contador) + "º - " + j[0] + "\t ---> " + str(j[1]) + "\n"
        text = "Click para ver todas las stats"
        url = "http://therealshow.rf.gd/"
        keyboard = [[InlineKeyboardButton("Enlace Stats completas", url = url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            chat_id=update.message.chat_id,
            text=textStat,
            parse_mode= ParseMode.MARKDOWN,
            reply_markup = reply_markup
        )
        #Cerrar la conexion SQL
        con.close()

#Comando para consultar la ficha
def mystats(bot, update, args):
    logger.info('He recibido un comando mystats de {}'.format (update.message.from_user.first_name))
    downloadDB()
    #Abrir conexion sql
    con = sqlite3.connect('therealshow.db')
    #Creamos un cursor
    cursorObj = con.cursor()
    #Almacenamos el id del usuario
    userid = update.message.from_user.id
    if(args):
        name = ""
        for p in args:
            name = name + p
        cursorObj.execute('SELECT idtelegram FROM jugador WHERE UPPER(nombre) IS UPPER("{}")'.format(name))
        jugadorsolicitado = cursorObj.fetchall()
        if( not jugadorsolicitado):
            bot.send_message(
                chat_id=update.message.chat_id,
                text="❌ Error: El jugador que estás consultando no existe o no tenemos datos. Quizá se llame de otra manera...",
                parse_mode= ParseMode.MARKDOWN
            )
            con.close()
            return 0
        else:
            userid = jugadorsolicitado[0][0]
    #Consulta para sacar las stats de un jugador
    cursorObj.execute('SELECT nombre, ngoles, nasistencias, pganados, pempates, pjugados, img FROM jugador WHERE idtelegram IS {}'.format(userid))
    #Samos todas las columnas de la consulta
    datosmyStatsJugadores = cursorObj.fetchall()
    #Cerrar la conexion SQL
    con.close()
    #Si la consulta no reporta ningun valor
    if(not datosmyStatsJugadores):
        bot.send_message(
                chat_id=update.message.chat_id,
                text="❌ Error: No tienes datos sobre tus estadísticas.❌ \n En breve te darán de alta \n {} ID: \t {}".format(update.message.from_user.first_name, update.message.from_user.id),
                parse_mode= ParseMode.MARKDOWN
            )
    #Si consulta es correcta
    else:
        #Sacar el jugador
        j = datosmyStatsJugadores[0]
        downloadCard(j[5])
        #Mostrar mensaje
        senderText = "📊 Stats de {} Season 2 📊\n".format(j[0])
        bot.send_photo(chat_id=update.message.chat_id, photo=open(j[5], 'rb'), caption =senderText + "\n\t🥇 Goles : " + str(j[1]) + "\n\t🥈 Asist: " + str(j[2]) + "\n\t🥉 P. Ganados: " + str(j[3]) + "\n\t 😑Empates: " + str(j[4]) + "\n\t🥺 P. Perdidos: " + str(j[5]-j[3]) + "\n\t⚽ P. Jugados: " + str(j[5]))

#Comando para mostrar los partidos asistidos
#R
def mypartidos(bot, update):
    logger.info('He recibido un comando mypartidos de {}'.format(update.message.from_user.first_name))
    #Comprobar si esta registrado
    #Si no esta registrado
    if(not isRegister(update.message.from_user.id)):
        bot.send_message(
            chat_id=update.message.chat_id,
            text=wellcomeText,
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        #Consulta para obtener el id del jugador
        cursorObj.execute('SELECT idjugador, nombre FROM jugador WHERE idtelegram is {}'.format(update.message.from_user.id))
        #Sacamos el id
        jugador = cursorObj.fetchall()
        #Consulta para sacar los partidos en los que participó
        cursorObj.execute('SELECT tematica, partido, equipo, goles, asistencias FROM resultado WHERE idjugador IS {} ORDER BY idresultado ASC'.format(jugador[0][0]))
        #Samos todas las columnas de la consulta
        datosPartidosJugador = cursorObj.fetchall()
        #Preparar el mensaje
        textStat = "*⚽️Partidos jugados por {}⚽️*\n\n".format(jugador[0][1])
        for partido in datosPartidosJugador:
            #Consulta para sacar las tematicas de los partidos en los que participó
            cursorObj.execute('SELECT tematica FROM partido WHERE idpartido IS {}'.format(partido[1]))
            #Samos todas las columnas de la consulta
            datosPartido = cursorObj.fetchall()
            textStat = textStat + "📂{}\n".format(datosPartido[0][0])
            #Datos concretos de cada jugador
            textStat = textStat + "     Ŀ—›▫️{}\n".format(partido[0])
            textStat = textStat + "         Ŀ—›🏆GOL:{}   🏅ASIS:{}\n".format(partido[3], partido[4])
        bot.send_message(
            chat_id=update.message.chat_id,
            text=textStat,
            parse_mode= ParseMode.MARKDOWN
        )
        con.close()

#Comando para mostrar una gráfica de los partidos
#R
def partidos(bot, update):
    logger.info('He recibido un comando partidos de {}'.format(update.message.from_user.first_name))
    #Comprobar si esta registrado
    #Si no esta registrado
    if(not isRegister(update.message.from_user.id)):
        bot.send_message(
            chat_id=update.message.chat_id,
            text=wellcomeText,
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        #Abrir conexion sql
        con = sqlite3.connect('therealshow.db')
        #Creamos un cursor
        cursorObj = con.cursor()
        #Consulta para obtener el id del jugador
        cursorObj.execute('SELECT tematica, fecha, hora, lugar FROM partido')
        partidos = cursorObj.fetchall()
        con.close()
        textStat = "*⚽️Partidos The Real Show S2⚽️*\n\n"
        for partido in partidos:
            textStat = textStat + "📂{}  {}  {}\n".format(partido[0], partido[1], partido[2])
        bot.send_message(
            chat_id=update.message.chat_id,
            text=textStat,
            parse_mode= ParseMode.MARKDOWN
        )

#Comando para mostrar una gráfica de los partidos
#R
def graph(bot, update, args):
    logger.info('He recibido un comando graph de {}'.format (update.message.from_user.first_name))
    #Comprobar si está registrado
    if(not isRegister(update.message.from_user.id)):
        bot.send_message(
            chat_id=update.message.chat_id,
            text=wellcomeText,
            parse_mode= ParseMode.MARKDOWN
        )
    else:
        idtelegram = update.message.from_user.id
        #Compare
        if(args):
            name = ""
            for p in args:
                name = name + p
            #Extraer los ids de los dos jugadores a comparar
            #Abrir conexion sql
            con = sqlite3.connect('therealshow.db')
            #Creamos un cursor
            cursorObj = con.cursor()
            #Consulta para sacar el id de un jugador
            cursorObj.execute('SELECT idjugador, nombre FROM jugador WHERE idtelegram IS "{}"'.format(idtelegram))
            #Samos todas las columnas de la consulta
            idjugador1 = cursorObj.fetchall()
            #Consulta para sacar el id de un jugador
            cursorObj.execute('SELECT idjugador, nombre FROM jugador WHERE UPPER(nombre) IS UPPER("{}")'.format(name))
            #Samos todas las columnas de la consulta
            idjugador2 = cursorObj.fetchall()
            if(not idjugador2 or idjugador1 == idjugador2):
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="❌ Error: El jugador que estás consultando no existe o eres tu mismo, prueba a escribirlo mejor.",
                    parse_mode= ParseMode.MARKDOWN
                )
                return 0
            else:
                #Consulta para sacar los resultados en los partidos donde jugo el jugador1
                cursorObj.execute('SELECT partido, goles, asistencias FROM resultado WHERE idjugador IS "{}"'.format(idjugador1[0][0]))
                #Samos todas las columnas de la consulta
                resultadosj1 = cursorObj.fetchall()
                #Consulta para sacar los resultados en los partidos donde jugo el jugador2
                cursorObj.execute('SELECT partido, goles, asistencias FROM resultado WHERE idjugador IS "{}"'.format(idjugador2[0][0]))
                #Samos todas las columnas de la consulta
                resultadosj2 = cursorObj.fetchall()
                #Consulta para sacar los partidos totales de la season
                cursorObj.execute('SELECT partidos FROM season WHERE idseason IS 1')
                #Samos todas las columnas de la consulta
                partidosseason = cursorObj.fetchall()
                #Parseamos los datos para construir la gráfica
                encuentro = list()
                encuentronombre = list()
                goles1 = list()
                asist1 = list()
                goles2 = list()
                asist2 = list()
                mejorgol = []
                mejorasist = []
                diferenciagoles = []
                diferenciaasist = []
                for resul1 in resultadosj1:
                    for resul2 in resultadosj2:
                        if (resul1[0] == resul2[0]):
                            #Consulta para sacar los encuentros en los partidos donde jugo el jugador
                            cursorObj.execute('SELECT tematica FROM partido WHERE idpartido IS "{}"'.format(resul1[0]))
                            #Samos todas las columnas de la consulta
                            tematicapartido = cursorObj.fetchall()
                            encuentronombre.append(tematicapartido[0][0])
                            encuentro.append(resul1[0])
                            goles1.append(resul1[1])
                            asist1.append(resul1[2])
                            goles2.append(resul2[1])
                            asist2.append(resul2[2])
                            if(not diferenciagoles or max(resul1[1]-resul2[1], resul2[1]-resul1[1]) > diferenciagoles[1]):
                                if(resul1[1]>resul2[1]):
                                    mejor = idjugador1[0][1]
                                else:
                                    mejor = idjugador2[0][1]
                                diferenciagoles = [tematicapartido[0][0], max(resul1[1]-resul2[1], resul2[1]-resul1[1]), mejor]
                            if(not diferenciaasist or max(resul1[2]-resul2[2], resul1[2]-resul1[2]) > diferenciaasist[1]):
                                if(resul1[2]>resul2[2]):
                                    mejor = idjugador1[0][1]
                                else:
                                    mejor = idjugador2[0][1]
                                diferenciaasist = [tematicapartido[0][0], max(resul1[2]-resul2[2], resul2[2]-resul1[2]), mejor]
                #Cerrar la conexion SQL
                con.close()
                if(not encuentronombre):
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="❌ Error: no tienes ningun partido en común con este jugador ❌",
                        parse_mode= ParseMode.MARKDOWN
                    )
                    return 0
                #Grafico Goles
                fig, (ax1, ax2) = plt.subplots(2, sharex=True)
                ax1.plot(encuentronombre, goles1, '.-', label='{}'.format(idjugador1[0][1]), linewidth=2,markersize=5)
                ax1.plot(encuentronombre, goles2, '.-', label='{}'.format(idjugador2[0][1]), linewidth=1,markersize=5)
                fig.suptitle('The Real Show GOLES-> {} vs {}'.format(idjugador1[0][1],idjugador2[0][1]))
                #Grafico Asist
                ax2.plot(encuentronombre, asist1, '.-', label='{}'.format(idjugador1[0][1]), linewidth=2,markersize=5)
                ax2.plot(encuentronombre, asist2, '.-', label='{}'.format(idjugador2[0][1]), linewidth=1,markersize=5)
                plt.xticks(rotation=90)
                plt.ylabel('Cantidades')
                plt.xlabel('Encuentros')
                fig.legend()
                plt.subplots_adjust(bottom=0.5)
                plt.savefig('tempgraph.png')
                bot.send_photo(chat_id=update.message.chat_id, photo=open('tempgraph.png', 'rb'), caption = "\n*Máxima diferencia de goles:*\n📂{}\n   🏆Goles: {}   🔝 {}\n*Máxima diferencia en asistencias:*\n📂{}\n   🏅Asist: {}   🔝{}".format(diferenciagoles[0],diferenciagoles[1],diferenciagoles[2],diferenciaasist[0], diferenciaasist[1],diferenciaasist[2]), parse_mode= ParseMode.MARKDOWN)
                plt.clf()
                plt.cla()
        #Simple
        else:
            #Abrir conexion sql
            con = sqlite3.connect('therealshow.db')
            #Creamos un cursor
            cursorObj = con.cursor()
            #Consulta para sacar el id de un jugador
            cursorObj.execute('SELECT idjugador, nombre FROM jugador WHERE idtelegram IS "{}"'.format(idtelegram))
            #Samos todas las columnas de la consulta
            idjugador = cursorObj.fetchall()
            #Consulta para sacar los resultados en los partidos donde jugo el jugador
            cursorObj.execute('SELECT partido, goles, asistencias FROM resultado WHERE idjugador IS "{}"'.format(idjugador[0][0]))
            #Samos todas las columnas de la consulta
            resultados = cursorObj.fetchall()
            #Parseamos los datos para construir la gráfica
            encuentro = list()
            goles = list()
            asist = list()
            mejorgol = []
            mejorasist = []
            for partido in resultados:
                #Consulta para sacar los encuentros en los partidos donde jugo el jugador
                cursorObj.execute('SELECT tematica FROM partido WHERE idpartido IS "{}"'.format(partido[0]))
                #Samos todas las columnas de la consulta
                tematicapartido = cursorObj.fetchall()
                encuentro.append(tematicapartido[0][0])
                goles.append(partido[1])
                asist.append(partido[2])
                if(not mejorgol or mejorgol[1] < partido[1]):
                    mejorgol = [tematicapartido[0][0],partido[1]]
                if(not mejorasist or mejorasist[1] < partido[2]):
                    mejorasist = [tematicapartido[0][0], partido[2]]
            #Cerrar la conexion SQL
            con.close()
            plt.subplots_adjust(bottom=0.5)
            plt.plot(encuentro, goles, '.-', label='Goles', linewidth=2,markersize=5)
            plt.plot(encuentro, asist, '.-', label='Asist', linewidth=1,markersize=5)
            plt.xticks(rotation=90)
            plt.title('The Real Show -> {}'.format(idjugador[0][1]))
            plt.ylabel('Cantidades')
            plt.xlabel('Encuentros')
            plt.legend()
            plt.savefig('tempgraph.png')
            bot.send_photo(chat_id=update.message.chat_id, photo=open('tempgraph.png', 'rb'), caption = "\n*Máximos goles en partido:*\n📂{}\n   🏆Goles:{}\n*Máximas asistencias en partido:*\n📂{}\n   🏅Asist:{}".format(mejorgol[0],mejorgol[1],mejorasist[0], mejorasist[1]), parse_mode= ParseMode.MARKDOWN)
            plt.clf()
            plt.cla()

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
'''
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
                if(statsaux[2] == '1'):
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
'''
#------------------------------------------------Funcion principal--------------------------------------------------------------------------------------------------
#Main Function
if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('alta', alta, pass_args=True))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('mystats', mystats, pass_args=True))
    dispatcher.add_handler(CommandHandler('partidos', partidos))
    dispatcher.add_handler(CommandHandler('mypartidos', mypartidos))
    dispatcher.add_handler(CommandHandler('mygraph', graph, pass_args=True))
    #dispatcher.add_handler(CommandHandler('season', season, pass_args=True))
    #dispatcher.add_handler(CommandHandler('convocar', convocar, pass_args=True))
    #dispatcher.add_handler(CommandHandler('apuntarse', apuntarse, pass_args=True))
    #dispatcher.add_handler(CommandHandler('equipos', equipos))
    #dispatcher.add_handler(CommandHandler('subirstats', subirStats, pass_args=True))

    run(updater)