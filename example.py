# -*- coding: utf-8 -*-
# Example chr url shortener setup script - this will just configure
# stuff, to run it use something like gunicorn:
#   gunicorn -b 127.0.0.1:5000 -p /tmp/chr.pid example:app

# Want to run multiple chr instances side by side? - see docs
# import chrso
# chrso.redis_namespace = "chr"

# Setup your secret key - otherwise things will break.. badly.
from chrso.main import app
app.config.update({
    "SECRET_KEY": "testing_testing_123",
})

# Do you have reCAPTCHA?
app.config.update({
    "RECAPTCHA_PUBLIC_KEY": "6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J",
    "RECAPTCHA_PRIVATE_KEY": "6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu"
})

# Is your app behind nginx, CloudFlare or something similar?
from chrso.proxyfix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, 1)

# Want to spruce up your chrso instance with a new name?
app.config.update({
	"CHR_HEADER": "foob.ar",
    "CHR_SUB_HEADER": "foo bar baz shortening",
})
