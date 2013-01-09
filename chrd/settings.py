# -*- coding: utf-8 -*-
# Settings file for chr url shortener.

# Don't ever enable debugging in a situation
# where the computer has a public IP.
debug = False


flask_debug = debug
flask_host = '127.0.0.1'
flask_port = 8080
flask_base = "/"
# Your shrunk URL formats. Use {slug} for
# where the url slug goes.
flask_url = "http://change.this/{slug}"
flask_secret_key = 'SOMETHING!SECRET@AND#HARD$TO%GUESS'

# Set this once, make it long and hard, and never change it.
salt_password = 'SOMETHING!UNIQUE@AND#HARD$TO%GUESS^OR&ELSE'

# Disable this if you're really security concious.
# With it on, people will be able to get the IP of
# your server. This is bad if you're behind CloudFlare
# or some other load balancer.
# With this disabled, urls are validated with a regex.
validate_urls = True
# The regex to validate urls if the above is False.
# It's intentionally sparse, we don't need a full fledged regex.
# DON'T CHANGE if you don't understand regexes.
#  Basically, this just handles urls like:
	# http://example.com
	# https://example.com
	# https://ssl.example.org
	# http://this.is.an.example.net/test.php
	# https://some-stupid.domain.co.nz/blah/is_a/word!
	# <stupidly long google images result that people always link>
validate_regex = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.!&()=:;?,-]*)\/?$'

# Soft cap for URL length. So people can't waste space.
# Besides, when is a URL ever *this* long?
soft_url_cap = 512

# Absolute directory for logging.
log_dir = "/path/to/logs"


# This has to be absolute or sqlite will complain.
sql_path = "/path/to/chr.db"

# reCAPTCHA settings.
captcha_public_key = "YOUR_PUBLIC_API_KEY"
captcha_private_key = "YOUR_PRIVATE_API_KEY"


# API stuff, for when we finish this.
api_enabled = False


#--------------------------#
# Constants (do not touch) #
#--------------------------#

# _SCHEMA_* are the table names.
# This allows simple changement of table names without changing 500 classes.
_SCHEMA_USERS = 'users'
_SCHEMA_REDIRECTS = 'redirects'
_SCHEMA_CLICKS = 'clicks'
_SCHEMA_MAX_SLUG = 32 # soft limit, schema defines as TEXT.

# Prefix for custom slugs.
# If it's more than one character, you WILL break things.
_CUSTOM_CHAR = '+'