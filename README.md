**BOT DE LINUX EN UBUNTU/DEBIAN**

- **El bot está en actualización !!**

aún no funciona del todo sin hacer ajustes manuales del lado del servidor

actualmente está ajustado solo para mi uso y tiene que editar el código cada uno dependiendo el uso que le den

edita main.py y completa los datos del bot, id usuario, id grupo, link grupo/canal, api ip-hash

- **Comandos**
```
/shell = ejecuta comando que tiene salida rápido con un ls, cat, mkdir, rm, df -h y otros
/cmd = ejecuta comandos largos y y dinámicos como wget, ffmpeg encoding, y otros pero mayormente descargas de archivos y comando que necesitan tiempo de ejecución y salidas largas
/compress -crf 24 = comprimir videos mp4 controlando crf 720p
/commpress2pass = comprimir vídeo con bitrate de 460k en 2 pasadas, el resultado es un video de 24 min de anime en 90MB de 720p
```
- **Necesario para shell y cmd**

nada, se usa directamente

- **Necesario para encoder**

**Instalación**

instalar Ffmpeg
```
sudo apt install ffmpeg
```

Herramienta para subir y descargar archivos de telegram, seguir los pasos para registrar su cuenta
```
pip install -U telegram-upload
```

Crear carpetas necesarios
```
mkdir encoder && cd encoder && mkdir encoded
```

agregar una imagen para su marca de agua en cada carpeta creado con el nombre de marca.png de una altura de más o menos 500px
y un archivo de subtitulo para la marca de agua del vídeo con el combre de marca_bot.ass

- **Estructura General del Bot**
```
tgbot_shell_encoder/
|  main.py
|  encoder/
|  |  marca.png
|  |  marca_bot.ass
|  |  encoded/
|  |  |  marca.png
|__|__|__marca_bot.ass
```
