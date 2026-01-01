import re, math, logging, secrets, time, mimetypes
import aiofiles
import os
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from info import *
from web.server import multi_clients, work_loads, kit_stream_bot
from web.server.exceptions import FIleNotFound, InvalidHash
from web.utils.custom_dl import ByteStreamer
from utils import get_readable_time
from web.utils import StartTime, __version__
from web.utils.render_template import render_page

routes = web.RouteTableDef()
class_cache = {}

@routes.get("/", allow_head=True)
async def root_route_handler(_):
    try:
        template_file = os.path.join("web", "template", "index.html")
        async with aiofiles.open(template_file, mode='r') as f:
            content = await f.read()
        return web.Response(text=content, content_type="text/html")
    except Exception as e:
        logging.error(f"Error loading landing page: {e}")
        return web.json_response({
            "server_status": "running",
            "uptime": get_readable_time(time.time() - StartTime),
            "telegram_bot": "@" + BOT_USERNAME,
            "connected_bots": len(multi_clients),
            "version": __version__,
        })


@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def stream_watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(
            text=await render_page(id, secure_hash), content_type="text/html"
        )
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        return web.Response(status=400, text="Bad Request")
    except Exception as e:
        logging.critical(e)
        return web.Response(status=500, text=str(e))

@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        return web.Response(status=400, text="Bad Request")
    except Exception as e:
        logging.critical(e)
        return web.Response(status=500, text=str(e))

async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range", None)

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    if MULTI_CLIENT:
        logging.info(f"📡 Client {index} is now serving: {request.remote}")

    tg_connect = class_cache.get(faster_client) or ByteStreamer(faster_client)
    class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        try:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            from_bytes = int(match.group(1))
            until_bytes = int(match.group(2)) if match.group(2) else file_size - 1
        except Exception:
            return web.Response(status=400, text="Invalid Range header")
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    # Validate range
    if until_bytes >= file_size or from_bytes < 0 or until_bytes < from_bytes:
        return web.Response(
            status=416,
            text="416: Range Not Satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"}
        )

    # Setup stream vars
    chunk_size = 1024 * 1024
    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    req_length = until_bytes - from_bytes + 1

    mime_type = file_id.mime_type or "application/octet-stream"
    file_name = file_id.file_name or f"{secrets.token_hex(2)}.bin"

    response = web.StreamResponse(
        status=206 if range_header else 200,
        reason="Partial Content" if range_header else "OK",
        headers={
            "Content-Type": mime_type,
            "Content-Length": str(req_length),
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }
    )

    await response.prepare(request)

    try:
        async for chunk in tg_connect.yield_file(
            file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
        ):
            await response.write(chunk)
    except Exception as e:
        logging.exception(f"Error streaming file {file_id.file_unique_id}: {e}")
    finally:
        await response.write_eof()

    return response


# ==========================================
# ADMIN DASHBOARD ROUTES
# ==========================================

import hashlib
import hmac
from database.users_db import db
from info import ADMINS, BOT_TOKEN, BOT_USERNAME

# Admin session storage (simple in-memory, use redis for production)
admin_sessions = {}

def verify_telegram_auth(auth_data: dict) -> bool:
    """Verify Telegram login widget data"""
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False
    
    # Create data check string
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items())]
    data_check_string = "\n".join(data_check_arr)
    
    # Create secret key from bot token
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    
    # Calculate hash
    calculated_hash = hmac.new(
        secret_key, 
        data_check_string.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == check_hash

def is_admin(user_id: int) -> bool:
    """Check if user is in ADMINS list"""
    return user_id in ADMINS

@routes.get("/admin/login")
async def admin_login_handler(request: web.Request):
    """Admin login page"""
    try:
        template_file = os.path.join("web", "template", "login.html")
        async with aiofiles.open(template_file, mode='r') as f:
            content = await f.read()
        content = content.replace("{{bot_username}}", BOT_USERNAME)
        return web.Response(text=content, content_type="text/html")
    except Exception as e:
        logging.error(f"Error loading login page: {e}")
        return web.Response(text="Error loading login page", status=500)

@routes.get("/admin/auth")
async def admin_auth_handler(request: web.Request):
    """Handle Telegram OAuth callback"""
    query_params = dict(request.rel_url.query)
    
    if not query_params:
        raise web.HTTPBadRequest(text="No auth data")
    
    # Verify the auth data
    auth_data = query_params.copy()
    user_id = int(auth_data.get('id', 0))
    
    if not verify_telegram_auth(auth_data.copy()):
        raise web.HTTPForbidden(text="Invalid authentication")
    
    if not is_admin(user_id):
        raise web.HTTPForbidden(text="You are not authorized to access admin panel")
    
    # Create session
    session_id = secrets.token_urlsafe(32)
    admin_sessions[session_id] = {
        "user_id": user_id,
        "username": auth_data.get('username', ''),
        "first_name": auth_data.get('first_name', 'Admin'),
        "auth_date": auth_data.get('auth_date')
    }
    
    # Redirect to admin with session cookie
    response = web.HTTPFound('/admin')
    response.set_cookie('admin_session', session_id, max_age=86400, httponly=True)
    return response

def get_admin_session(request: web.Request):
    """Get admin session from cookie"""
    session_id = request.cookies.get('admin_session')
    if session_id and session_id in admin_sessions:
        return admin_sessions[session_id]
    return None

@routes.get("/admin")
async def admin_dashboard_handler(request: web.Request):
    """Admin dashboard page"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPFound('/admin/login')
    
    try:
        template_file = os.path.join("web", "template", "admin.html")
        async with aiofiles.open(template_file, mode='r') as f:
            content = await f.read()
        return web.Response(text=content, content_type="text/html")
    except Exception as e:
        logging.error(f"Error loading admin page: {e}")
        return web.Response(text="Error loading admin page", status=500)

@routes.get("/admin/logout")
async def admin_logout_handler(request: web.Request):
    """Logout admin"""
    session_id = request.cookies.get('admin_session')
    if session_id and session_id in admin_sessions:
        del admin_sessions[session_id]
    
    response = web.HTTPFound('/admin/login')
    response.del_cookie('admin_session')
    return response

# Admin API Routes
@routes.get("/admin/api/stats")
async def admin_api_stats(request: web.Request):
    """Get dashboard statistics"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    stats = await db.get_admin_stats()
    stats["uptime"] = get_readable_time(time.time() - StartTime)
    stats["connected_clients"] = len(multi_clients)
    stats["version"] = __version__
    return web.json_response(stats)

@routes.get("/admin/api/files")
async def admin_api_files(request: web.Request):
    """Get files list"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    page = int(request.rel_url.query.get('page', 1))
    search = request.rel_url.query.get('search', '')
    result = await db.get_files_paginated(page=page, search=search)
    return web.json_response(result)

@routes.delete("/admin/api/files/{file_id}")
async def admin_api_delete_file(request: web.Request):
    """Delete a file from database AND Telegram"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    file_id = request.match_info['file_id']
    
    # Delete from Telegram BIN_CHANNEL
    try:
        await kit_stream_bot.delete_messages(chat_id=BIN_CHANNEL, message_ids=int(file_id))
        logging.info(f"Deleted message {file_id} from BIN_CHANNEL")
    except Exception as e:
        logging.error(f"Failed to delete from Telegram: {e}")
    
    # Delete from database
    await db.delete_file_by_id(file_id)
    return web.json_response({"success": True})

@routes.get("/admin/api/users")
async def admin_api_users(request: web.Request):
    """Get users list"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    page = int(request.rel_url.query.get('page', 1))
    result = await db.get_users_paginated(page=page)
    return web.json_response(result)

@routes.post("/admin/api/users/{user_id}/ban")
async def admin_api_ban_user(request: web.Request):
    """Ban a user"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    user_id = int(request.match_info['user_id'])
    await db.block_user(user_id, reason="Banned by admin")
    return web.json_response({"success": True})

@routes.post("/admin/api/users/{user_id}/unban")
async def admin_api_unban_user(request: web.Request):
    """Unban a user"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    user_id = int(request.match_info['user_id'])
    await db.unblock_user(user_id)
    return web.json_response({"success": True})

@routes.get("/admin/api/premium")
async def admin_api_premium(request: web.Request):
    """Get premium users list"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    result = await db.get_premium_users_list()
    return web.json_response(result)

@routes.post("/admin/api/premium/{user_id}")
async def admin_api_add_premium(request: web.Request):
    """Add premium to user"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    user_id = int(request.match_info['user_id'])
    try:
        data = await request.json()
        days = data.get('days', 30)
    except:
        days = 30
    
    await db.add_premium_access(user_id, days)
    return web.json_response({"success": True})

@routes.delete("/admin/api/premium/{user_id}")
async def admin_api_remove_premium(request: web.Request):
    """Remove premium from user"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    user_id = int(request.match_info['user_id'])
    await db.remove_premium_access(user_id)
    return web.json_response({"success": True})

@routes.get("/admin/api/banned")
async def admin_api_banned(request: web.Request):
    """Get banned users list"""
    session = get_admin_session(request)
    if not session:
        raise web.HTTPUnauthorized(text="Not authenticated")
    
    result = await db.get_banned_users_list()
    return web.json_response(result)

