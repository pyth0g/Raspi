from flask import Blueprint, render_template, request, make_response, jsonify, redirect, send_file
import resources
import RPi.GPIO as gpio
from datetime import datetime as dt, timezone, timedelta
import psutil
import math
from time import sleep
import re
import hashlib
import qrcode
import base64
import io
from PIL import Image

gpio.setwarnings(False)

gpio.setmode(gpio.BOARD)
pins = [15, 16]

gpio.setup(pins, gpio.OUT)

views = Blueprint(__name__, "views")

@views.route("/")
def index():
    return render_template('index.html')

@views.route("/led", methods=['GET', 'POST'])
def led():
    if request.method == 'POST':
        state = request.form

        if "led_red" in state:
            # red
            gpio.output(pins, (gpio.HIGH, gpio.LOW))

        elif "led_green" in state:
            # green
            gpio.output(pins, (gpio.LOW, gpio.HIGH))

        elif "led_off" in state:
            # off
            gpio.output(pins, (gpio.LOW, gpio.LOW))

    return render_template('led.html')

@views.route("/led_message", methods=['GET', 'POST'])
def led_message():
    if request.method == 'POST':
            text = request.form.to_dict()['message']
            time = request.form.to_dict()['time']
            try: time = float(time)
            except: time = 0.4

            now = dt.now()
            
            if text:
                with open("messages.log", "a") as f:
                    f.write(f"{now.date()} [{now.hour}:{now.minute}:{now.second}] {text}\n")

            for l in text:
                for i in '{0:08b}'.format(ord(l)):
                    if i == "0":
                        #green
                        gpio.output(pins, (gpio.LOW, gpio.HIGH))

                        sleep(time)
                        gpio.output(pins, (gpio.LOW, gpio.LOW))
                        sleep(time)

                    elif i == "1":
                        # red
                        gpio.output(pins, (gpio.HIGH, gpio.LOW))

                        sleep(time)
                        gpio.output(pins, (gpio.LOW, gpio.LOW))
                        sleep(time)

    return render_template('led_message.html')

@views.route("/time")
def time():
    response = resources.Digital.time()

    if "text/html" in request.headers.get("Accept", ""):
        return render_template('time.html', time=resources.Digital.time())

    return response, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@views.route("/clock")
def clock():
    response = resources.Clock().clock() + "\n"

    if "text/html" in request.headers.get("Accept", ""):
        return render_template('clock.html', time=resources.Clock().clock())

    return response, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@views.route("/calendar")
def calendar():
    def is_mobile(user_agent):
        mobile_agents = re.compile(r".*(iphone|android|mobile|ipad|tablet|blackberry|nokia|windows phone).*", re.IGNORECASE)
        return bool(mobile_agents.match(user_agent))

    user_agent = request.headers.get("User-Agent", "").lower()

    response = resources.Calendar.calendar() + "\n"
    
    if "text/html" in request.headers.get("Accept", ""):
        return render_template('calendar.html', time=resources.Calendar.calendar(weird_display = True if is_mobile(user_agent) else False))

    return response, 200, {'Content-Type': 'text/plain; charset=utf-8'}

def format_size(size_bytes):
   if size_bytes == 0:
       return "0 B"
   
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)

   return f"{s} {size_name[i]}"

@views.route("/sysinfo")
def sysinfo():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    cpu_temp = resources.cpu_temp()

    sys_info = {
        "cpu_usage": cpu_usage,
        "cpu_temp": cpu_temp,
        "memory_total": format_size(memory_info.total),
        "memory_used": format_size(memory_info.used),
        "memory_free": format_size(memory_info.free),
        "disk_total": format_size(disk_info.total),
        "disk_used": format_size(disk_info.used),
        "disk_free": format_size(disk_info.free),
    }

    response = f"""CPU: {cpu_usage}%
CPU Temperature: {cpu_temp}°C

Total Memory: {format_size(memory_info.total)}
Used Memory: {format_size(memory_info.used)}
Free Memory: {format_size(memory_info.free)}

Total Disk: {format_size(disk_info.total)}
Used Disk: {format_size(disk_info.used)}
Free Disk: {format_size(disk_info.free)}
"""

    if "text/html" in request.headers.get("Accept", ""):
        return render_template('sysinfo.html', sys_info=sys_info)
    
    return response, 200, {'Content-Type': 'text/plain; charset=utf-8'}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def lookup_hash(page: str) -> str:
    try:
        with open("qrd.urls", "r") as f:
            urls = {i.split(" ")[0]: i.split(" ")[1:] for i in f.read().split("\n")}
            try:
                hash = urls[page][1]
            except KeyError:
                hash = "*"

    except FileNotFoundError:
        hash = "*"

    return hash

def qrd_get(element: str) -> list[str]:
    try:
        with open("qrd.urls", "r") as f:
            for i in f.read().split("\n"):
                if i.split(" ")[0] == element:
                    return i.split(" ")
                
            return None

    except FileNotFoundError:
        pass

def qrd_update(element: str, path: str = None, hash: str = None):
    try:
        with open("qrd.urls", "r") as f:
            content = f.read()
            content = [i.split(" ") for i in content.split("\n")]
            for c, i in enumerate(content):
                if i[0] == element:
                    content[c] = [content[c][0], path if path else content[c][1], hash if hash else content[c][2]]

            content = "\n".join([" ".join(i) for i in content])

        with open("qrd.urls", "w") as f:
            f.write(content)

    except FileNotFoundError:
        pass

@views.route('/verify-auth/<path:page>', methods=['POST'])
def verify_auth(page):
    hash = lookup_hash(page)

    if hash != "*":
        client_auth = request.cookies.get(page)

        if not client_auth:
            return make_response(jsonify({"message": "Unauthorized: No auth cookie"}), 401)
        
        server_auth = hash + hash_password(str(dt.now(timezone.utc).day))
        
        if client_auth != server_auth:
            return make_response(jsonify({"message": "Unauthorized"}), 401)

    return make_response(jsonify({"message": "Authenticated"}), 200)
    
@views.route('/verify-login/<path:page>', methods=['POST'])
def verify_login(page):
    data = request.json
    submitted_hash = data.get('password')

    hash = lookup_hash(page)

    if submitted_hash == hash or hash == "*":
        auth_token = hash + hash_password(str(dt.now(timezone.utc).day))

        resp = make_response(jsonify({"message": "Authenticated"}))
        resp.set_cookie(page, auth_token, httponly=True, secure=True, samesite='Lax', path='/')

        return resp
    else:
        return make_response(jsonify({"message": "Incorrect password"}), 401)

@views.route("/qrd/handler/<path:page>", methods=['GET', 'POST'])
def qrd_handler(page):
    if verify_auth(page).status_code == 401:
        return render_template('login.html', page=page)
    
    if request.method == 'POST':
        req = list(map(str.lower, request.form.to_dict()))
        if "logout" in req:
            resp = make_response(redirect(f"/qrd/config/{page}"))
            resp.set_cookie(page, '', expires=0)

            return resp
        
        elif "password" in req:
            return render_template('change_password.html', page=page)
        
        elif "new_password" in req:
            new = request.form.to_dict()['new_password']
            if new != request.form.to_dict()['confirm_password']:
                return render_template('change_password.html', page=page, error="The passwords entered don't match.")
            
            new_hash = hash_password(new)
            qrd_update(page, hash=new_hash)

            return redirect(f"/qrd/handler/{page}")

        elif "page" in req:
            with open("qrd.url", "w+") as f:
                url = request.form.to_dict()['page']

                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url

                qrd_update(page, url)
    
    return render_template('admin.html', page=page)

@views.route("/qrd/<path:page>")
def qrd_serve(page):
    try:
        with open("qrd.urls", "r") as f:
            urls = {i.split(" ")[0]: i.split(" ")[1:] for i in f.read().split("\n")}
            try:
                url = urls[page][0]
            except KeyError:
                url = "/qrd"

    except FileNotFoundError:
        url = "/"

    return redirect(url)

@views.route("/qrd/config/<path:page>")
def qrd_config(page):
    if verify_auth(page).status_code == 401:
        return render_template('login.html', page=page)
    
    return render_template('admin.html', page=page)

def qr_code(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        box_size=5,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode('utf-8')

qrd_banned = ["config", "handler", "admin", "update", "login", "create"]

class qrdCreate:
    def __init__(self):
        self.page = ""
        self.b64im = ""

    def qrd_create(self):
        if request.method == 'POST':
            req = list(map(str.lower, request.form.to_dict()))

            if "new" in req:
                if not str(request.form.to_dict()['new']).isalnum() or str(request.form.to_dict()['new']) == qrd_banned or qrd_get(request.form.to_dict()['new']):
                    return render_template('qrd-create.html', img_data="", error="This path already exists or is not allowed.", vis="hidden")
                    
                url = f"https://raspi.kladnik.cc/qrd/{request.form.to_dict()['new']}"

                with open("qrd.urls", "a") as f:
                    f.write(f"{request.form.to_dict()['new']} /qrd/config/{request.form.to_dict()['new']} *\n")

                self.page = request.form.to_dict()['new']
                self.b64im = qr_code(url)

                return render_template('qrd-create.html', img_data=f"data:image/png;base64,{self.b64im}", link=url, t1="Link:", t2="QR Code:", vis="submit")
            
            elif "save_qr" in req:
                img = Image.open(io.BytesIO(base64.b64decode(self.b64im)))
                img_io = io.BytesIO()

                img.save(img_io, 'PNG')
                img_io.seek(0)

                return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"qr_code_{self.page}.png")

        return render_template('qrd-create.html', img_data="", vis="hidden")

qrdcreate = qrdCreate()    

@views.route("/qrd", methods=['GET', 'POST'])
def qrd_create():
    return qrdcreate.qrd_create()

def counter_file(values=[]):
    with open("ctr.inf", "r+") as f:
        contents = f.read()

        f.seek(0)
        if values:
            f.write("\n".join(values))

        elif not contents:
            f.write(f"0\n{str(dt.now())}\n{contents.split("\n")[2]}")
            contents = f"0\n{str(dt.now())}\n{contents.split("\n")[2]}"

    return contents.split("\n")

@views.route("/ctr", methods=['GET', 'POST'])
def counter():
    last = dt.strptime(counter_file()[1], '%Y-%m-%d %H:%M:%S')
    since = int((dt.now() - last).days)
    freezes = int(counter_file()[2])

    if since != 0:
        if since > 1:
            if int(counter_file()[2]) > 0:
                count = counter_file()[0]
                counter_file([count, str(dt.now() - timedelta(days=1)).split('.')[0], str(freezes - 1)])
                return render_template('counter.html', count=str(count), color="rgb(32, 176, 244)", img="static/flame-freeze.png")

            else:
                counter_file(["0", str(dt.now() - timedelta(days=1)).split('.')[0], str(freezes)])
    
        else:
            if request.method == 'POST':
                counter_file([str(int(counter_file()[0]) + 1), str(dt.now()).split('.')[0], str(freezes)])
                since = 0

    count = counter_file()[0]
    
    if since == 0:
        return render_template('counter.html', count=str(count), color="rgb(247, 144, 1)", img="static/flame.png")
        
    else:
        return render_template('counter.html', count=str(count), color="rgb(158, 158, 158)", img="static/flame-off.png")
        