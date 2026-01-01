import os, sys, glob, pytz, asyncio, logging, importlib
from pathlib import Path
from pyrogram import idle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)
 
from info import *
from typing import Union, Optional, AsyncGenerator
from Script import script 
from datetime import date, datetime 
from aiohttp import web
from web import web_server, check_expired_premium
from web.server import kit_stream_bot
from utils import temp, ping_server
from web.server.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)
kit_stream_bot.start()
loop = asyncio.get_event_loop()

async def start():
    print('\n')
    print('Initializing KitStream Bot...')
    bot_info = await kit_stream_bot.get_me()
    await initialize_clients()
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Imported => " + plugin_name)

    if ON_HEROKU:
        asyncio.create_task(ping_server())
    me = await kit_stream_bot.get_me()
    temp.BOT = kit_stream_bot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    tz = pytz.timezone('Asia/Kuala_Lumpur')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    kit_stream_bot.loop.create_task(check_expired_premium(kit_stream_bot))
    
    # Start web server FIRST before sending messages
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    logging.info(f"Web Server Started at port {PORT}")
    
    # Send startup messages (non-blocking, wrapped in try-except)
    try:
        await kit_stream_bot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    except Exception as e:
        logging.error(f"Failed to send to LOG_CHANNEL: {e}")
    
    try:
        await kit_stream_bot.send_message(chat_id=ADMINS[0], text='<b>KitStream Bot Restarted!!</b>')
    except Exception as e:
        logging.error(f"Failed to send to ADMIN: {e}")
    
    try:
        await kit_stream_bot.send_message(chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>")
    except Exception as e:
        logging.error(f"Failed to send to SUPPORT_GROUP: {e}")
    
    logging.info("KitStream Bot Started Successfully!")
    await idle()

if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('----------------------- KitStream Service Stopped -----------------------')
