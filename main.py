import logging
import asyncio
import subprocess
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client as tgClient, filters, enums
from pytz import utc
import pyrogram
import psutil
import time
import psutil
from tqdm import tqdm
import datetime
import os
import pty
import asyncio
# Lista para mantener un registro de los procesos en ejecución
TELEGRAM_API = ""
TELEGRAM_HASH = ""
BOT_TOKEN = "" 

#####################################################################################
#####################################################################################
# variables principales
MI_CHAT_ID =   #id de usuario, completar
Admin = 2096120369 #id de un usuario admin
GRUPO = -100

# Define una variable global para almacenar el proceso
shell_tasks = {}
#   Lista de Habilitados para usar el bot
#---grupos:
SUDOS= (MI_CHAT_ID,Admin,)
GRUPOS_STAFF = (GRUPO,)
# Obtiene la ruta del directorio actual donde se encuentra el script bot.py
current_directory = os.path.dirname(os.path.abspath(__file__))
#####################################################################################
#mension en nombre
#user_mention = message.from_user.mention(style="html") if message.from_user else ""
#####################################################################################
# Configuración del registro
from logging import basicConfig, FileHandler, StreamHandler, INFO
basicConfig(format="[%(asctime)s] [%(levelname)s] - %(message)s",
            datefmt="%d-%b-%y %I:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)
# Creación del cliente de Pyrogram
bot = tgClient('botsh', TELEGRAM_API, TELEGRAM_HASH, bot_token=BOT_TOKEN, workers=1000,
               parse_mode=enums.ParseMode.HTML)
# Inicio del programador asincrónico
scheduler = AsyncIOScheduler(timezone=utc)
#####################################################################################
#####################################################################################
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""
    await message.reply_text(
        f"{user_mention} ¡Hola! Soy un bot en desarrollo.\n<i>/help más detalles...</i>",
        reply_to_message_id=message.id
        )

@bot.on_message(filters.command("help"))
async def start_command(client, message):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""
    await message.reply_text(
        f"{user_mention} Detalles extras:\npara mas info de este bot comunicarse con @Jhon_Wilmer_JK\n[𝙔𝙖𝙞𝙘𝙝𝙞_𝙅𝙆㉿𝘽𝙤𝙩 ] <b>v1.35.0</b>",
        reply_to_message_id=message.id
        )


# Función para ejecutar comandos en el shell de forma asíncrona
async def run_shell_command(command):
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        return stdout.decode(), stderr.decode()

    except asyncio.CancelledError:
        process.kill()
        raise

# Comando de shell
@bot.on_message(filters.command("shell"))
async def shell_command(client, message):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""

    # Extraer el comando del mensaje
    command = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not command:
        await message.reply("Por favor, proporciona un comando para ejecutar en el shell.")
        return

    # Ejecutar el comando en el shell
    stdout, stderr = await run_shell_command(command)

    # Comprobar el tamaño del stdout
    if len(stdout) > 4096:  # Límite aproximado de caracteres en Telegram
        # Crear un archivo temporal para el stdout
        file_path = f'std_out_{message.id}.txt'
        with open(file_path, 'w') as file:
            file.write(stdout)
        
        # Enviar el archivo al usuario
        await message.reply_document(file_path, caption=f"{user_mention}\n<b>Resultados del comando:</b>\n<b>stdout:</b> (guardado en archivo)\n<b>stderr:</b>\n<code>{stderr}</code>")
        
        # Eliminar el archivo después de enviarlo
        os.remove(file_path)
    else:
        # Enviar resultados al usuario directamente
        response = f"{user_mention}\n<b>Resultados del comando:</b>\n\n"
        response += "<b>stdout:</b>\n"
        response += f"<code>{stdout}</code>\n\n"
        response += "<b>stderr:</b>\n"
        response += f"<code>{stderr}</code>\n"

        await message.reply_text(response, reply_to_message_id=message.id)



############################################################################################################
# Función para obtener la información del disco
def get_disk_info():
    partitions = psutil.disk_partitions()
    disk_usage = psutil.disk_usage('/')
    total_disk = disk_usage.total
    free_disk = disk_usage.free
    used_disk = disk_usage.used
    return total_disk, free_disk, used_disk

############################################################################################################
############################################################################################################
# Función para descargar un video con seguimiento de progreso
async def shell_process(client, message, cmd):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""
    user_id = message.from_user.id
    #cmd = message.text
    logging.info("---iniciando subproceso---")
    logging.info(f"parametros: {cmd}")
    progress_message = await message.reply_text(f"<b>{cmd}</b> \n"
                                                  f"<b>┠ Status:</b> En cola...\n"
                                                  f"<b>┠ Speed:</b> 0.00 MiB/s <b>| Elapsed:</b> 0m 0s\n"
                                                  f"<b>┠ Info:</b> shell en bash\n"
                                                  f"<b>┠ Mode:</b> #shell | #pty.fork\n"
                                                  f"<b>┠ User:</b> {user_mention} <b>| ID:</b> <code>{user_id}</code> \n"
                                                  f"<b>┖</b> cancel_en_espera",
                                                  reply_to_message_id=message.id,
                                                  disable_web_page_preview=True)
    # Configura el descriptor de archivo en modo no bloqueante
    comando = cmd
    # Iniciar el proceso con pty.fork()
    pid, fd = pty.fork()
    if pid == 0:
        # Niño
        os.execlp('bash', 'bash', '-c', comando)
    else:
        # Padre
        proceso_descarga = pid
        shell_tasks[progress_message.id] = asyncio.current_task()  # Almacena la tarea actual en el diccionario
        start_time = time.time()
        last_update_time = start_time
        video_size = None
        video_folder = None
        percentage = None
        while proceso_descarga is not None:
            await asyncio.sleep(0.1)  # Permitir que otras tareas se ejecuten
            try:
                salida = os.read(fd, 1024).decode('utf-8')
                if not salida:
                    pass
                logging.info(f"OUTOPUT: {salida}")
                # Verificar valores inválidos


                # Obtener la información del disco
                total_disk, free_disk, used_disk = get_disk_info()
                disk_percentage = (used_disk / total_disk) * 100
                # Obtener la hora del sistema
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Obtener el uso de la CPU
                cpu_usage = psutil.cpu_percent(interval=1)
                #tiempo elapsed
                elapsed_time = round(time.time() - start_time)
                elapsed_minutes = int(elapsed_time // 60)
                elapsed_seconds = int(elapsed_time % 60)

                # Obtener las últimas 10 líneas de la salida
                salida_lines = salida.splitlines()[-10:]
                # Unir las líneas en una sola cadena nuevamente
                salida_10l = '\n'.join(salida_lines)

                if int(elapsed_time) % 7 == 0 and time.time() - last_update_time >= 7:
                    await progress_message.edit_text(f"<b><i>{cmd}</i></b>\n"
                                                    f"<b>┠ Status:</b> subprocess...\n"
                                                    f"<b>┠ Elapsed:</b> {elapsed_minutes}m {elapsed_seconds}s\n"
                                                    f"<b>┠ Info:</b> shell en bash \n"
                                                    f"<b>┠</b><code> /cancel_shell {progress_message.id}</code>\n"
                                                    f"<b>┠──────────────────────</b>\n"
                                                    f"<pre language='shell'>{salida_10l}</pre>\n"
                                                    f"<b>┠──────────────────────</b>\n"
                                                    f"<b>⌬  BOT STATISTICS: </b>{current_time}\n"
                                                    f"<b>┠ CPU: </b>{cpu_usage:.1f}%\n"
                                                    f"<b>┠ OS Uptime: </b>{datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))}\n"
                                                    f"<b>┖ U: </b>{used_disk / (1024 ** 3):.2f}GB <b>| F: </b>{free_disk / (1024 ** 3):.2f}GB<b> | T: </b>{total_disk / (1024 ** 3):.2f}GB"
                                                    )
            except OSError as e:
                if e.errno == 5:  # Error de E/S (entrada/salida)
                    break
                else:
                    raise  # Re-lanza la excepción si no es un error de E/S
            except Exception as e:
                logging.error(f"Error de shell: {str(e)}")


@bot.on_message(filters.command("cmd"))
async def descargar_video_command(client, message):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""
    if message.chat.id in GRUPOS_STAFF or message.from_user.id in SUDOS:
        if len(message.command) >= 2:
            comando = message.text.split()
            #cmd = comando[1:]
            cmd = ' '.join(comando[1:])
            #await message.reply_text(f"<b>{user_mention} Información:</b>\n/encoding es un comando para encodear videos con -c:v libx264 -crf 20, pero el comando está restringido a uso Premium", reply_to_message_id=message.id)
            await shell_process(client, message, cmd)
        else:
            await message.reply_text(f"{user_mention} Proporciona un cmd", reply_to_message_id=message.id)
    else:
        await message.reply_text(f"{user_mention}❌ No autorizado 🚫", reply_to_message_id=message.id)



################# CANCEL #################################3333

async def cancelar_descarga_por_mensaje(message_id, message):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""
    task = shell_tasks.get(message_id)
    if task:
        task.cancel()
        del shell_tasks[message_id]
        await message.reply_text(f"<b>Subprocess Stopped!</b>\n"
                                 f"┠ Task for: {user_mention}\n"
                                 f"┠ Due To: ¡Comando detenido!\n"
                                 f"┃ \n"
                                 f"┠ Mode: #Shell | #pty.fork\n"
                                 f"┖ Elapsed: None",
                                 reply_to_message_id=message.id)
        await bot.delete_messages(message.chat.id, message_id)
        logging.info("Descarga detenida...")
    else:
        await message.reply_text("No se encontró ninguna subprocess con el message_id proporcionado.", reply_to_message_id=message.id)
@bot.on_message(filters.command("cancel_shell"))
async def cancelar_descarga_command(client, message):
    if len(message.command) == 1:
        # Si el comando no tiene argumentos, agregar el ID del mensaje actual al comando
        await message.reply_text(f"Por favor, proporciona el <code>message_id</code> del proceso que deseas cancelar.\nEjemplo: <code>/cancel_shell 123</code>", reply_to_message_id=message.id)
        return
    try:
        message_id = int(message.command[1])
    except ValueError:
        await message.reply_text("Por favor, proporciona un message_id válido.", reply_to_message_id=message.id)
        return
    await cancelar_descarga_por_mensaje(message_id, message)


############################################################################################################
############################################################################################################
descarga_tasks = {}
# Función para descargar un video con seguimiento de progreso
async def download_video(client, message, message2,param):
    ubicacion = 'encoder/marca.png'
    if not os.path.exists(ubicacion):
        cmd_marca = f'cd encoder && wget https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjFA-jPETEHVcHYARdjsZWmUqCkTK70CDFlduqSxgoa4gUXQCvKDcvJQqsoKPmm7ECku-NFHU0LUrDAy-YbxCw1eQOGMRmIFqBJSg9_yyQXqhj8ohUTLWt1TvOmYrvwnp1gVmhyphenhyphenDifTd5CuvOjoFiwgTCnw2GoSLT2BnLbcb-nyU3utoW0rhiMBhT09THSA/s16000/marca.png'
        await asyncio.create_subprocess_shell(cmd_marca)

    user_mention = message2.from_user.mention(style="html") if message.from_user else ""
    user_id = message2.from_user.id
    info="Encode | -c:v libx264 -crf 20"
    enlace_html = f"<a href='t.me/Yaichi_Anime'>link</a>"
    # Verifica si el mensaje tiene un video adjunto
    if message.video:
        download_dir = "encoder"
        video_name = message.video.file_name
        # Crea el directorio de descarga si no existe
        os.makedirs(download_dir, exist_ok=True)
        # Construye la ruta completa del archivo
        file_path = os.path.join(download_dir, video_name)
        progress_message = await message.reply_text(f"<b>{video_name}</b> \n"
                                                    f"┃ [□□□□□□□□□□□□□] 00.00%\n"
                                                    f"<b>┠ Status:</b> En cola...\n"
                                                    f"<b>┠ Speed:</b> 0.00 MiB/s <b>| Elapsed:</b> 0m 0s\n"
                                                    f"<b>┠ Info:</b> Encode | -c:v libx264 -crf {param}\n"
                                                    f"<b>┠ Mode:</b> #Leech | #Pyrogram\n"
                                                    f"<b>┠ User:</b> {user_mention} <b>| ID:</b> <code>{user_id}</code> \n"
                                                    f"<b>┖</b> cancel_en_espera",
                                                    reply_to_message_id=message2.id,
                                                    disable_web_page_preview=True)
        descarga_tasks[progress_message.id] = asyncio.current_task()  # Almacena la tarea actual en el diccionario

        # Descarga el video con seguimiento de progreso
        await message.download(file_name=file_path, progress=progress_down_callback(progress_message,video_name, user_mention, user_id,))
        logging.info("Video descargado exitosamente!")
        await progress_message.edit_text(f"<b>✅ Video descargado exitosamente‼️</b>\n<i>⚙️ INICIANDO ENCODING 📉</i>")
        logging.info("---iniciando encoding")
        time.sleep(1)
        video_res2 = f"{current_directory}/encoder/HD_{video_name}"
        video_res3 = f"{current_directory}/encoder/HDL_{video_name}"
        # Configura el descriptor de archivo en modo no bloqueante
                
        # Comando ffmpeg
        comandos = f'cd encoder && mkdir -p encoded && ' \
                f'ffmpeg -i "{video_name}" -filter_complex "[0:v]split=2[v1];[v1]ass=./marca_bot.ass[v1out]" ' \
                f'-map "[v1out]" -map 0:a -c:v libx264 -s 1280x720 -crf 26 -preset fast -tune animation -profile:v high -c:a copy "{video_res2}" -y && ' \
                f'ffmpeg -i "{video_res2}" -ss 00:01:00 -s 1280x720 -frames:v 1 "{video_res2}_fondo.jpg" -y && ' \
                f'ffmpeg -i "{video_res2}_fondo.jpg" -i "marca.png" -filter_complex "[1:v]scale=iw/2:-1 [marca_scaled]; [0:v][marca_scaled]overlay=W-w-10:H-h-10" "{video_res2}_min.jpg" -y && ' \
                f'telegram-upload -i --thumbnail-file "{video_res2}_min.jpg" "{video_res2}" --to https://t.me/+OyZLcyRrDuszZGJh && ' \
                f'ffmpeg -i "{video_res2}" -an -vcodec libx264 -vb 460k -pass 1 -passlogfile "2pass_{video_res2}.log" -profile:v high10 -tune animation -preset medium -s 1280x720 "{current_directory}/encoder/encoded/HDL_{video_name}" && ' \
                f'rm "{current_directory}/encoder/encoded/HDL_{video_name}" && ' \
                f'ffmpeg -i "{video_res2}" -c:a aac -ab 70k -ac 2 -ar 22050 -vcodec libx264 -vb 460k -pass 2 -passlogfile "2pass_{video_res2}.log" -profile:v high10 -tune animation -preset slow -s 1280x720 -scodec copy -map 0 "{current_directory}/encoder/encoded/HDL_{video_name}" && ' \
                f'rm "2pass_{video_res2}.log*" && ' \
                f'telegram-upload -i --thumbnail-file "{video_res2}_min.jpg" "{current_directory}/encoder/encoded/HDL_{video_name}" --to https://t.me/+OyZLcyRrDuszZGJh -d'


        comando = f'cd encoder && ' \
                f'ffmpeg -i "{video_name}" -map 0:v -map 0:a -c:v libx264 -s 1280x720 -crf {param} -preset medium -tune animation -profile:v high -c:a copy "v2_{video_name}" && ' \
                f'ffmpeg -i "v2_{video_name}" -ss 00:01:00 -s 1280x720 -frames:v 1 "v2_{video_name}_fondo.jpg" -y && ' \
                f'ffmpeg -i "v2_{video_name}_fondo.jpg" -i "marca.png" -filter_complex "[1:v]scale=iw/2:-1 [marca_scaled]; [0:v][marca_scaled]overlay=W-w-10:H-h-10" "v2_{video_name}_min.jpg" -y && ' \
                f'telegram-upload -i --thumbnail-file "v2_{video_name}_min.jpg" "v2_{video_name}" --to https://t.me/+OyZLcyRrDuszZGJh -d && ' \
                f'rm "v2_{video_name}_fondo.jpg" && rm "v2_{video_name}_min.jpg" '



        print(f"bash ==> {comando}")

        # Iniciar el proceso con pty.fork()
        pid, fd = pty.fork()
        if pid == 0:
            # Niño
            os.execlp('bash', 'bash', '-c', comando)
        else:
            # Padre
            proceso_descarga = pid
            descarga_tasks[progress_message.id] = asyncio.current_task()  # Almacena la tarea actual en el diccionario
            start_time = time.time()
            last_update_time = start_time
            video_size = None
            video_folder = None
            percentage = None
            while proceso_descarga is not None:
                await asyncio.sleep(0.1)  # Permitir que otras tareas se ejecuten
                try:
                    salida = os.read(fd, 1024).decode('utf-8')
                    if not salida:
                        pass
                    print(f"[00-Apr-00 12:59:59 AM] [OUTP] - {salida}")
                    # Verificar valores inválidos
                    if "No such file or directory" in salida:
                        await progress_message.edit_text(f"ERROR interno:\nNo such file or directory")
                        return
                    else:
                        pass
                    if "invalid value entered." in salida:
                        await progress_message.edit_text(f"ERROR interno:\n{salida}")
                        return
                    else:
                        pass

                    # Obtener la información del disco
                    total_disk, free_disk, used_disk = get_disk_info()
                    disk_percentage = (used_disk / total_disk) * 100
                    # Obtener la hora del sistema
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Obtener el uso de la CPU
                    cpu_usage = psutil.cpu_percent(interval=1)
                    #tiempo elapsed
                    elapsed_time = round(time.time() - start_time)
                    elapsed_minutes = int(elapsed_time // 60)
                    elapsed_seconds = int(elapsed_time % 60)

                    pattern = r"video:(\d+)kB"
                    match = re.search(pattern, salida)
                    if match:
                        size_kb = int(match.group(1))
                        if size_kb >= 1024 * 1024:  # Si el tamaño es mayor o igual a 1 GB
                            video_size = f"{size_kb / (1024 * 1024):.2f} GB"
                        elif size_kb >= 1024:  # Si el tamaño es mayor o igual a 1 MB
                            video_size = f"{size_kb / (1024):.2f} MB"
                        else:
                            video_size = f"{size_kb:.2f} KB"
                    else:
                        pass

                    # Obtener las últimas 10 líneas de la salida
                    salida_lines = salida.splitlines()[-10:]
                    # Unir las líneas en una sola cadena nuevamente
                    salida_10l = '\n'.join(salida_lines)
                    #print(f"------video_size: {video_size}")
                    video_folder2 = f"{video_res2}"
                    video_folder3 = f"{video_res3}"
                    #print(f"----------videofolder:{video_folder}")
                    if int(elapsed_time) % 7 == 0 and time.time() - last_update_time >= 7:
                        await progress_message.edit_text(f"<b><i>{video_res2}</i></b>\n"
                                                        f"<b>┠ Status:</b> Encoding...\n"
                                                        f"<b>┠ Elapsed:</b> {elapsed_minutes}m {elapsed_seconds}s\n"
                                                        f"<b>┠ Info:</b> -c:v libx264 -crf 20 \n"
                                                        f"<b>┠</b><code> /cancel_down {progress_message.id}</code>\n"
                                                        f"<b>┠──────────────────────</b>\n"
                                                        f"<pre language='shell'>{salida_10l}</pre>\n"
                                                        f"<b>┠──────────────────────</b>\n"
                                                        f"<b>⌬  BOT STATISTICS: </b>{current_time}\n"
                                                        f"<b>┠ CPU: </b>{cpu_usage:.1f}%\n"
                                                        f"<b>┠ OS Uptime: </b>{datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))}\n"
                                                        f"<b>┖ U: </b>{used_disk / (1024 ** 3):.2f}GB <b>| F: </b>{free_disk / (1024 ** 3):.2f}GB<b> | T: </b>{total_disk / (1024 ** 3):.2f}GB"
                                                        )
                except OSError as e:
                    if e.errno == 5:  # Error de E/S (entrada/salida)
                        break
                    else:
                        raise  # Re-lanza la excepción si no es un error de E/S
                except Exception as e:
                    logging.error(f"Error en el Encoding: {str(e)}")
            os.remove(f"encoder/{video_name}")
            logging.info(video_folder2)
            logging.info(video_folder3)
            #await progress_message.edit_text(f"v2_{video_name} ver en")


def progress_down_callback(progress_message, video_name, user_mention, user_id):
    start_time = time.time()  # Guardar el tiempo de inicio
    last_update_time = start_time  # Guardar el último tiempo de actualización
    async def callback(current, total):
        nonlocal last_update_time  # Declarar last_update_time como no local
        percentage = (current / total) * 100
        elapsed_time = time.time() - start_time  # Calcular el tiempo transcurrido
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)
        # Verificar si ha pasado un múltiplo de 10 segundos desde la última actualización
        if int(elapsed_time) % 10 == 0 and time.time() - last_update_time >= 10:
            last_update_time = time.time()  # Actualizar el último tiempo de actualización
            # Calcular la velocidad de subida
            current_speed = measure_upload_speed()
            current_speed_formatted = format_speed(current_speed)
            # Calcular el progreso de la barra
            progress_bar_length = 13
            progress_bar = ''.join(['■' if i * (100 / progress_bar_length) <= percentage else '□' for i in range(progress_bar_length)])
            # Editar el mensaje con el progreso actual y el tiempo transcurrido
            await progress_message.edit_text(
                f"<b>{video_name}</b> \n"
                f"┃ [{progress_bar}] {percentage:.2f}%\n"
                f"<b>┠ Processed:</b> {format_size(current)} of {format_size(total)}\n"
                f"<b>┠ Status:</b> Downloading\n"
                f"<b>┠ Speed:</b> {current_speed_formatted} <b>| Elapsed:</b> {elapsed_minutes}m {elapsed_seconds}s\n"
                f"<b>┠ Info:</b> Encode | -c:v libx264 -crf 20\n"
                f"<b>┠ Mode:</b> #Leech | #Ffmpeg\n"
                f"<b>┠ User:</b> {user_mention} <b>| ID:</b> <code>{user_id}</code> \n"
                f"<b>┖</b><code> /cancel_down {progress_message.id}</code>"
            , disable_web_page_preview=True)
        logging.info(f"Downloading: {percentage:.2f}% | Elapsed: {elapsed_minutes}m {elapsed_seconds}s | {video_name}")
    return callback



@bot.on_message(filters.command("compress") & filters.reply)
async def descargar_video_command(client, message):
    user_mention = message.from_user.mention(style="html") if message.from_user else ""
    command_parts = message.text.split()

    # Verifica si el comando es correcto
    if len(command_parts) != 3 or command_parts[1] != '-crf' or not command_parts[2].isdigit():
        await message.reply_text(f"{user_mention} Comando inválido. Uso correcto: <code>/compress -crf [número]</code>", reply_to_message_id=message.id)
        return

    param = int(command_parts[2])

    if message.chat.id in GRUPOS_STAFF or message.from_user.id in SUDOS:
        # Verifica si el mensaje al que se responde es un video
        if message.reply_to_message and message.reply_to_message.video:
            # Llama a la función para descargar el video
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage >= 70.0:
                await message.reply_text(f"<b>{user_mention} ⚠️ Servidor ocupado, intente más tarde‼️</b>\n<b>CPU: </b>{cpu_usage:.1f}%\n", reply_to_message_id=message.id)
            else:
                await download_video(client, message.reply_to_message, message, param)
        else:
            await message.reply_text(f"{user_mention} Por favor, responde a un video para descargarlo.", reply_to_message_id=message.id)
    else:
        await message.reply_text(f"{user_mention}❌ No autorizado 🚫", reply_to_message_id=message.id)


def format_size(size_in_bytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    index = 0
    while size_in_bytes >= 1024 and index < len(suffixes) - 1:
        size_in_bytes /= 1024.0
        index += 1
    return f"{size_in_bytes:.2f} {suffixes[index]}"

def format_speed(speed_in_kib):
    speed_in_mib = speed_in_kib / 1024.0
    suffixes = ['KiB/s', 'MiB/s', 'GiB/s', 'TiB/s', 'PiB/s']
    index = 0
    while speed_in_mib >= 1024 and index < len(suffixes) - 1:
        speed_in_mib /= 1024.0
        index += 1
    return f"{speed_in_mib:.2f} {suffixes[index]}"

# Función de callback para el progreso del video
def upload_progress_callback(progress_message, video_name, file_size, user_mention, user_id, enlace_html, info):
    start_time = time.time()  # Guardar el tiempo de inicio
    last_update_time = start_time  # Guardar el último tiempo de actualización
    async def callback(current, total):
        nonlocal last_update_time  # Declarar last_update_time como no local
        percentage = (current / total) * 100
        elapsed_time = time.time() - start_time  # Calcular el tiempo transcurrido
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)
        # Verificar si ha pasado un múltiplo de 10 segundos desde la última actualización
        if int(elapsed_time) % 10 == 0 and time.time() - last_update_time >= 10:
            last_update_time = time.time()  # Actualizar el último tiempo de actualización
            # Calcular la velocidad de subida
            current_speed = measure_upload_speed()
            current_speed_formatted = format_speed(current_speed)
            # Calcular el progreso de la barra
            progress_bar_length = 13
            progress_bar = ''.join(['■' if i * (100 / progress_bar_length) <= percentage else '□' for i in range(progress_bar_length)])
            # Editar el mensaje con el progreso actual y el tiempo transcurrido
            await progress_message.edit_text(
                f"<b>{video_name}</b> \n"
                f"┃ [{progress_bar}] {percentage:.2f}%\n"
                f"<b>┠ Processed:</b> {format_size(current)} of {format_size(file_size)}\n"
                f"<b>┠ Status:</b> Uploading\n"
                f"<b>┠ Speed:</b> {current_speed_formatted} <b>| Elapsed:</b> {elapsed_minutes}m {elapsed_seconds}s\n"
                f"<b>┠ Info:</b> {enlace_html} | {info}\n"
                f"<b>┠ Mode:</b> #Leech | #Pyrogram\n"
                f"<b>┠ User:</b> {user_mention} <b>| ID:</b> <code>{user_id}</code> \n"
                f"<b>┖</b><code> /cancel_upload {progress_message.id}</code>"
            , disable_web_page_preview=True)
        logging.info(f"Uploading: {percentage:.2f}% | Elapsed: {elapsed_minutes}m {elapsed_seconds}s | {video_name}")
    return callback

# Función para medir la velocidad de subida en bytes por segundo
def measure_upload_speed(duration=0.1, interval=0.1):
    start_time = time.time()
    start_bytes_sent = psutil.net_io_counters().bytes_sent
    time.sleep(duration)  # Espera el tiempo especificado
    end_time = time.time()
    end_bytes_sent = psutil.net_io_counters().bytes_sent
    total_time = end_time - start_time
    total_bytes_sent = end_bytes_sent - start_bytes_sent
    # Calcular la velocidad de subida promedio
    upload_speed = total_bytes_sent / total_time if total_time > 0 else 0
    return upload_speed

def miniatura(video_name, video_folder):
    try:
        if "HD" in video_folder:
            fondo_path = f'{current_directory}/encoder/{video_name}_fondo.jpg'
            marca_path = f'{current_directory}/encoder/marca.png'
            miniatura_path = f'{current_directory}/encoder/{video_name}_min.jpg'
            comando_ffmpeg = (
                f'cd {current_directory}/encoder && ffmpeg -i "{video_name}" -ss 00:01:00 -s 1280x720 -frames:v 1 "{video_name}_fondo.jpg" -y && '
                f'ffmpeg -i "{fondo_path}" -i "{marca_path}" -filter_complex "[1:v]scale=iw/2:-1 [marca_scaled]; [0:v][marca_scaled]overlay=W-w-10:H-h-10" "{video_name}_min.jpg" -y'
            )
            r = subprocess.run(comando_ffmpeg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            #print (r.stderr)
            return miniatura_path
        else:
            fondo_path = f'{current_directory}/videos/{video_name}_fondo.jpg'
            marca_path = f'{current_directory}/videos/marca.png'
            miniatura_path = f'{current_directory}/videos/{video_name}_min.jpg'
            comando_ffmpeg = (
                f'cd {current_directory}/videos && ffmpeg -i "{video_name}" -ss 00:01:00 -s 1280x720 -frames:v 1 "{video_name}_fondo.jpg" -y && '
                f'ffmpeg -i "{fondo_path}" -i "{marca_path}" -filter_complex "[1:v]scale=iw/2:-1 [marca_scaled]; [0:v][marca_scaled]overlay=W-w-10:H-h-10" "{video_name}_min.jpg" -y'
            )
            r = subprocess.run(comando_ffmpeg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            #print (r.stderr)
            return miniatura_path
    except Exception as e:
        logging.error(f"Error en miniatura de video: {str(e)}")




# #######№##########№
def main() -> None:
    try:
        print('Iniciando el Bot...')
        # Verificar si el bot ya está conectado antes de intentar iniciar
        if not bot.is_initialized:
            bot.start()
            print('Bot iniciado correctamente. Esperando mensajes...')
            # Iniciar un bucle infinito
            asyncio.get_event_loop().run_forever()
        else:
            print('El bot ya está conectado.')
    except KeyboardInterrupt:
        print('Se presionó Ctrl+C. Deteniendo el bot...')
        # Detener el bot antes de salir
        bot.stop()
    except asyncio.CancelledError:
        print("Tarea cancelada.")
    except Exception as e:
        print(f"Error al iniciar el bot: {str(e)}")
        # Puedes agregar un registro de errores aquí si lo deseas
if __name__ == '__main__':
    main()
