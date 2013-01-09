# -*- coding: utf-8 -*-
# chr's flask handler.

# flask stuff
from flask import Flask, render_template, session, abort, request, g
from flask import redirect, url_for, flash, make_response, jsonify
# recaptcha related
from recaptcha.client import captcha
# requests for url validation
import requests
# python modules
import re
import time
from datetime import datetime
# chr modules
import chru
import settings
import logger
import utility
import daemon

# revision() is in utility.py

app = Flask(__name__)
app.debug = settings.flask_debug
app.secret_key = settings.flask_secret_key
app.jinja_env.globals.update(sorted=sorted)
app.jinja_env.globals.update(len=len)
app.jinja_env.globals.update(date_strip_day=utility.date_strip_day)

# List of used routes, so we can't use it as a slug.
reserved = ('index', 'submit')

@app.route("/index")
@app.route("/")
def index():
	return render_template('index.html', recaptcha_key=settings.captcha_public_key)

@app.route("/<slug>")
def slug_redirect(slug):
	logger.debug("slug:", slug, 
				", valid:", chru.is_valid_slug(slug),
				", id:", chru.slug_to_id(slug),
				", exists:", chru.slug_exists(slug))
	if not chru.is_valid_slug(slug) or not chru.slug_exists(slug):
		return redirect(url_for('index'))
	url = chru.url_from_slug(slug)
	chru.add_hit(slug, request.remote_addr, request.user_agent)
	return redirect(url)

@app.route("/<slug>/delete/<delete>")
def slug_delete(slug, delete):
	logger.debug("delete slug:", slug,
				", valid:", chru.is_valid_slug(slug),
				", id:", chru.slug_to_id(slug),
				", exists:", chru.slug_exists(slug))
	if not chru.is_valid_slug(slug) or not chru.slug_exists(slug):
		return redirect(url_for('index'))
	row = chru.slug_to_row(slug)
	if delete != row['delete']:
		return redirect(url_for('index'))
	chru.delete_slug(slug)
	logger.info("Successfully deleted", settings.flask_url.format(slug=row['short']))
	flash("Successfully deleted {0}".format(settings.flask_url.format(slug=row['short'])), "success")
	return redirect(url_for('index'))

@app.route("/<slug>/stats")
def slug_stats(slug):
	if not chru.is_valid_slug(slug) or not chru.slug_exists(slug):
		return redirect(url_for('index'))
	row = chru.slug_to_row(slug)
	clicks = utility.sql().where('url', row['id']).get('clicks')

	click_info = {
		"platforms": {"unknown": 0},
		"browsers": {"unknown": 0},
		"pd": {}, # clicks per day
	}
	month_ago = int(time.time()) - (60 * 60 * 24 * 30) # Last 30 days
	month_ago_copy = month_ago
	for x in xrange(1, 31):
		# Prepopulate the per day clicks dictionary.
		# This makes life much much easier for everything.
		month_ago_copy += (60 * 60 * 24) # one day
		strf = str(datetime.fromtimestamp(month_ago_copy).strftime('%m/%d'))
		click_info['pd'][strf] = 0

	for click in clicks:
		if click['time'] > month_ago:
			# If the click is less than a month old
			strf = str(datetime.fromtimestamp(click['time']).strftime('%m/%d'))
			click_info['pd'][strf] += 1

		if len(click['agent']) == 0 \
				or len(click['agent_platform']) == 0 \
				or len(click['agent_browser']) == 0:
			click_info['platforms']['unknown'] += 1
			click_info['browsers']['unknown'] += 1
			continue

		platform_ = click['agent_platform']
		browser_ = click['agent_browser']
		if not platform_ in click_info['platforms']:
			click_info['platforms'][platform_] = 1
		else:
			click_info['platforms'][platform_] += 1
		if not browser_ in click_info['browsers']:
			click_info['browsers'][browser_] = 1
		else:
			click_info['browsers'][browser_] += 1
	print click_info

	# Yes, formatting in stuff without escaping it, I know, I'm bad!
	# But these are *safe* variables, we know they're good in advance.
	unique = utility.sql().query('SELECT COUNT(DISTINCT `{0}`) AS "{1}" FROM `{2}`'.format('ip', 'unq', settings._SCHEMA_CLICKS))
	unique = unique[0]['unq']
	rpt = len(clicks) - unique
	hits = {
		"all": len(clicks),
		"unique": unique,
		"return": rpt,
		"ratio": str(round(float(unique) / float(len(clicks)), 2))[2:] # (unique / all)% of visitors only come once.
	}

	stats = {
		"hits": utility.Struct(**hits),
		"clicks": utility.Struct(**click_info),
		"long": row['long'],
		"long_clip": row['long'],
		"short": row['short'],
		"short_url": settings.flask_url.format(slug=row['short'])
	}
	if len(row['long']) > 30:
		stats['long_clip'] = row['long'][:30] + '...'
	return render_template('stats.html', stats=utility.Struct(**stats))

@app.route("/submit", methods=["GET"])
def submit_get():
	return redirect(url_for('index'))

@app.route("/submit", methods=["POST"])
def submit():
	response = captcha.submit(
		request.form['recaptcha_challenge_field'],
		request.form['recaptcha_response_field'],
		settings.captcha_private_key,
		request.remote_addr
	)
	if not response.is_valid:
		data = {
			"error": "true",
			"message": "The captcha typed was incorrect.",
			"url": "",
			"delete": "",
			"given": request.form['chr_text_long']
		}
		return jsonify(data)

	if settings.validate_urls:
		try:
			logger.debug("Sending HEAD request to:", request.form['chr_text_long'])
			head = requests.head(request.form['chr_text_long'], timeout=1)
			logger.debug("Reply:", head.status_code, head.headers)
			if head.status_code == 404:
				raise requests.exceptions.HTTPError
		except requests.exceptions.InvalidSchema as e:
			logger.debug(e)
			data = {
				"error": "true",
				"message": "The URL provided was not valid.",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
		except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
			logger.debug(e)
			data = {
				"error": "true",
				"message": "The URL provided was unable to be found.",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
		except requests.exception.RequestException as e:
			logger.debug(e)
			data = {
				"error": "true",
				"message": "Something went wrong validating your URL.",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
	else:
		logger.debug("Matching '{0}' against '{1}'.".format(request.form['chr_text_long'], settings.validate_regex))
		if not re.match(settings.validate_regex, request.form['chr_text_long'], re.I):
			data = {
				"error": "true",
				"message": "The URL provided was not valid.",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)

	if len(request.form['chr_text_long']) > settings.soft_url_cap:
		# Soft cap so that people can't abuse it and waste space.
		data = {
			"error": "true",
			"message": "The given URL was actually <i>too</i> long to shrink.",
			"url": "",
			"delete": "",
			"given": request.form['chr_text_long']
		}
		return jsonfiy(data)

	custom_slug = False
	if len(request.form['chr_text_short']) > 0:
		slug_ = request.form['chr_text_short']
		if not re.match('^[\w -]+$', slug_):
			data = {
				"error": "true",
				"message": "The custom URL was invalid. Only alphanumeric characters, dashes, spaces and underscores, please!",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
		if len(slug_) > settings._SCHEMA_MAX_SLUG:
			data = {
				"error": "true",
				"message": "The custom URL given is too long. Less than 32 characters, please!",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
		if slug_ in reserved:
			data = {
				"error": "true",
				"message": "Sorry, that custom URL is reserved.",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
		if chru.slug_exists(settings._CUSTOM_CHAR + slug_):
			data = {
				"error": "true",
				"message": "Sorry, that custom URL already exists.",
				"url": "",
				"delete": "",
				"given": request.form['chr_text_long']
			}
			return jsonify(data)
		custom_slug = settings._CUSTOM_CHAR + slug_


	slug_, id_, delete_, url_, old_ = chru.url_to_slug(request.form['chr_text_long'], ip=request.remote_addr, slug=custom_slug)
	delete_ = settings.flask_url.format(slug=slug_) + "/delete/" + delete_
	delete_ = delete_ if 'chr_check_delete' in request.form \
						and request.form['chr_check_delete'] == "yes" \
						and not old_ \
						else ""
	data = {
		"error": "false",
		"message": "Successfully shrunk your URL!" if not old_ else "URL already shrunk, here it is!",
		"url": settings.flask_url.format(slug=slug_),
		"delete": delete_,
		"given": url_
	}
	return jsonify(data)

def run():
	check_sql()
	app.run(host=settings.flask_host, port=settings.flask_port)

def check_sql():
	# This is here because if it's in utilities, you get
	# an import loop, which is ugly.
	import os
	if os.path.isfile(settings.sql_path):
		return
	with open('chrd/schema/schema.sql', 'rb') as f:
		utility.sql()._cursor.executescript(f.read())
	sl = chru.url_to_slug("https://github.com/PigBacon/chr", slug=settings._CUSTOM_CHAR + "source")
	if sl:
		logger.info("Successfully setup SQL and added first redirect.")
		logger.debug(sl)

if __name__ == "__main__":
	run()