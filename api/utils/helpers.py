import re
import string
import random
from api.models import Url

def validate_name(name):
    return type(name) == str and len(name) > 1

def validate_email(email):
    if not (type(email) == str and re.match("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[-]?\w+[.]\w+$", email)):
        return None
    return True

def get_file_extension(filename):
    try:
        ext = re.search("\.[a-z]{2,5}$", filename).group()
    except:
        ext = ''
    return ext

def validate_password(password):
    return type(password) == str and len(password) >= 3

def validate_make_private(make_private):
    return make_private if type(make_private) == bool else None

def sanitize_short_url(url):
    if (not url) or type(url) != str: return None
    string_choice = string.ascii_letters + string.digits
    url = re.sub(r'^(http(s)?://)?(www.)?urrl.link/', '', url, flags=re.IGNORECASE)
    if not any(ch in string_choice for ch in url):
        return None
    return f"urrl.link/{url}"

def sanitize_long_url(url):
    if (not url) or type(url) != str: return None
    url = re.sub(r'^(http(s)?://)?(www.)?', 'https://', url, flags=re.IGNORECASE)
    if not (re.match("^((https?|ftp|file):\/\/)?[-A-Za-z0-9+&@#\/%?=~_|!:,.;]+[-A-Za-z0-9+&@#\/%=~_|]$", url) and ("." in url)):
        return None
    return url

def generate_short_url(url):
    string_choice = string.ascii_letters + string.digits
    short_url = "".join([random.choice(string_choice) for _ in range(7)])

    while Url.query.filter_by(short_url=short_url).first():
        short_url = "".join([random.choice(string_choice) for _ in range(7)])
    return f"urrl.link/{short_url}"

number_to_month = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec'
}