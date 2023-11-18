#!/usr/bin/env python3

# Requires `brew install translate-shell`
# and DEEPL_FREE_API_KEY or DEEPL_API_KEY environment variables set.

import os
import subprocess
import logging
import platform
import requests
import shutil
import sys

TRANS_CMD = 'trans'

# Use DeepL when possible with a fall back to Google.
# List of Google Translate target languages: https://cloud.google.com/translate/docs/languages
GOOGLE_TARGET_LANGUAGES = [
  'ar',
  'be',
  'ca',
  'es-MX',
  'eu',
  'fa',
  'he',
  'hi',
  'mr',
  'sw',
  'th',
  'vi',
  'zh-TW',  # zh-Hant in OM
  'af', # Below added by WB
  'bg',
  'cs' ,
  'da' ,
  'de',
  'el',
  'es',
  'et',
  'fi',
  'fr',
  'hr',
  'hu',
  'id',
  'it',
  'ja',
  'ko',
  'lt',
  'nb',
  'nl',
  'pl',
  'pt',
  'pt-BR',
  'ro',
  'ru',
  'sk',
  'sv',
  'tr',
  'uk',
  'zh', # zh-Hans in OM
]

# See https://www.deepl.com/docs-api/translate-text/translate-text/ for target languages.
DEEPL_TARGET_LANGUAGES = [
    'bg',
    'cs',
    'da',
    'de',
    'el',
    'en-GB',
    'en-US', # en in OM
    'es',
    'et',
    'fi',
    'fr',
    'hu',
    'id',
    'it',
    'ja',
    'ko',
#    'lt',
#    'lv',
    'nb',
    'nl',
    'pl',
    'pt-BR',
    'pt-PT',  # pt in OM
    'ro',
    'ru',
    'sk',
#    'sl',
    'sv',
    'tr',
    'uk',
    'zh',  # zh-Hans in OM
]


def get_api_key():
  key = os.environ.get('DEEPL_FREE_API_KEY')
  if key == None:
    key = os.environ.get('DEEPL_API_KEY')
  if key == None:
    print('Error: DEEPL_FREE_API_KEY or DEEPL_API_KEY env variables are not set')
    exit(1)
  return key

def google_translate(text, source_language):
  fromTo = source_language.lower() + ':'
  for lang in GOOGLE_TARGET_LANGUAGES:
    fromTo += lang + '+'
  # Remove last +
  fromTo = fromTo[:-1]
  res = subprocess.run([TRANS_CMD, '-b', '-no-bidi', fromTo, text], text=True, capture_output=True)
  if res.returncode != 0:
    print(f'Error running {TRANS_CMD} program:')
    print(res.stderr)
    exit(1)

  print('\nGoogle translations:')
  translations = {source_language: text}
  i = 0
  for line in res.stdout.splitlines():
    lang = GOOGLE_TARGET_LANGUAGES[i]
    if lang == 'zh-TW':
      lang = 'zh-Hant'
    elif lang == 'zh':
      lang = 'zh-Hans'
    translations[lang] = line.capitalize()
    i = i + 1
    print(lang + ' = ' + line)
  return translations

def deepl_translate_one(text, source_language, target_language):
  url = 'https://api-free.deepl.com/v2/translate'
  payload = {
      'text': text,
      'source_lang': source_language.lower(),
      'target_lang': target_language,
      'formality': 'prefer_less',
  }
  headers = {
      'Content-Type': 'application/json',
      'Authorization': 'DeepL-Auth-Key '+get_api_key(),
  }
  print(headers)

  try: # for Python 3
      from http.client import HTTPConnection
  except ImportError:
      from httplib import HTTPConnection
  HTTPConnection.debuglevel = 1
  
  logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
  logging.getLogger().setLevel(logging.DEBUG)
  requests_log = logging.getLogger("urllib3")
  requests_log.setLevel(logging.DEBUG)
  requests_log.propagate = True

  response = requests.request('POST', url, headers=headers, json=payload)
  print(response)
  json = response.json()
  return json['translations'][0]['text']

def deepl_translate(text, source_language):
  translations = {}
  print('Deepl translations:')
  for lang in DEEPL_TARGET_LANGUAGES:
    translation = deepl_translate_one(text, source_language, lang)
    if lang == 'pt-PT':
      lang = 'pt'
    elif lang == 'zh':
      lang = 'zh-Hans'
    elif lang == 'en-US':
      lang = 'en'
    translations[lang] = translation.capitalize()
    print(lang + ' = ' + translation)
  return translations

def usage():
  print('Usage:', sys.argv[0], 'Some English text to translate')
  print('For a custom source language add a two-letter code with a colon in the beginning:')
  print('      ', sys.argv[0], 'de:Some German text to translate')
  if shutil.which(TRANS_CMD) == None:
    print(TRANS_CMD, ' program for Google Translate is not installed.')
    if platform.system() == 'Darwin':
      print('Install it using `brew install translate-shell`')
    else:
      print('See https://www.soimort.org/translate-shell/ for installation instructions')

if __name__ == '__main__':
  if len(sys.argv) < 2:
    usage()
    exit(1)

  if not 'DEEPL_FREE_API_KEY' in os.environ and not 'DEEPL_API_KEY' in os.environ:
    print('Error: neither DEEPL_FREE_API_KEY nor DEEPL_API_KEY environment variables are set.')
    print('DeepL translations are not available. Register for a free Developer API account here:')
    print('https://www.deepl.com/pro#developer')
    print('and get the API key here: https://www.deepl.com/account/summary')
    exit(1)

  text_to_translate = ' '.join(sys.argv[1:])

  source_language = 'en'
  if len(text_to_translate) > 3 and text_to_translate[2] == ':':
    source_language = text_to_translate[0:2]
    text_to_translate = text_to_translate[3:].lstrip()

  #translations = deepl_translate(text_to_translate, source_language)
  translations = google_translate(text_to_translate, source_language)
  #translations.update(google_translations)
  # Remove duplicates for regional variations.
  for regional in ['en-GB', 'es-MX', 'pt-BR']:
    main = regional.split('-')[0]  # 'en', 'es', 'pt'...
    if translations.get(regional, 1) == translations.get(main, 0):
      translations.pop(regional)

  if not translations.get('en',False):
    print("English wasn't in the translations list despite being the source, that's weird. Debug.")
    exit(1)

  print('\nMerged Deepl and Google translations:')
  en = translations.pop('en')
  langs = list(translations.keys())
  langs.sort()

  print('============ categories.txt format ============')
  print('en:' + en)
  for lang in langs:
    print(lang + ':' + translations[lang])

  print('============ strings.txt format ============')
  print('    en =', en)
  for lang in langs:
    print('   ', lang, '=', translations[lang])
