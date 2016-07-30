#!/usr/bin/python3
# -*- coding:  utf-8 -*-

"""
    Запуск скрипта выполняется командой: $ python abit_donntu.py dump (Обычный дамп факультетов)
    Также можно задампить в json диапозон абитуриентов по photoid, например
        $ python abit_donntu.py dump_abit <start_id> <end_id>
        $ python abit_donntu.py dump_abit 1 3170 (скрипт будет работать ~1 часа)
"""
__version__ = '0.0.1'
__author__ = 'Yegorov <yegorov0725@yandex.ru>'

import sys
import requests
import json
import re
import datetime
import time
import random
from collections import OrderedDict


USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:47.0) "
              "Gecko/20100101 Firefox/47.0")

def get_json(url, referer):
    request = requests.get(url,
                           headers={
                               'Referer': referer,
                               'User-Agent': USER_AGENT
                           })
    data = request.json(object_pairs_hook=OrderedDict)
    return data

def get_file_name(name, ext="json"):
    return "{}_{}.{}".format(name, datetime.datetime.now().strftime("%Y-%m-%d"), ext)
    
def read_json(file_name, prefix="./data/"):
    d = None
    with open(prefix + file_name, 'r', encoding='utf-8') as fp:
        d = json.load(fp)
    return d

def write_json(file_name, d, prefix="./data/"):
    with open(prefix + file_name, 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(d, ensure_ascii=False, indent=2))
    
def helpers_dumps():
    """
    Возвращает словарь вида:
        {
            "faculties": [
                {
                    "id": ...
                    "name": ...
                },
                ...]
            "education_levels": [
                {
                    "id": ...
                    "name": ...
                },
                ...]
            "forms": [
                {
                    "id": ...
                    "name": ...
                },
                ...]
        }
    faculties - список факультетов
    education_levels - уровень образования (Бакалавр, ...)
    forms - форма обучения (дневная, ...)    
    """
    helper_dict = {}
    referer = "http://abit.donntu.org/"
    urls = {
                "education_levels": "http://abit.donntu.org/data/get_education_levels.php",
                "forms": "http://abit.donntu.org/data/get_forms.php",
                "faculties": "http://abit.donntu.org/data/get_faks.php"
           }
    for (key, url) in urls.items():
        helper_dict[key] = get_json(url, referer)
    return helper_dict

def write_helpers():
    """
    Записывает вспомогательные данные.
    Создает файл helpers_yyyy-mm-dd.json
    """
    write_json(get_file_name("helpers"), helpers_dumps())
    
def specs_dumps(education_level_id=-1, form_id=-1, faculty_id=-1):
    """
    Возвращает словарь специальностей, например:
        [
            {
            "id": 1083,
            "name": "Теплоэнергетика и теплотехника",
            "shifr": "13.03.01",
            "nameFak": "ФМФ",
            "nameFO": "дневная",
            "nameOU": "бакалавр",
            "kurs": 1
            },
            ...
        ]
    Функция принимает параметры: education_level_id - id уровня образования (Бакалавр, ...),
                                 form_id - id формы обучения (дневная, ...),
                                 faculty_id - id факультета
    Все эти id можно получить из helpers, 
    например для получения специальностей магистратуры КНТ всех форм обучения,
    вызов будет такой: specs_dumps(238, -1, 30)
    """
    # args = list(locals().values())
    # if args.count(-1) >= 3:
    #     raise Exception("Function must have minimum one argument not equals -1")
    if education_level_id == -1:
        raise Exception("Function must have education level argument")
    
    specs_dict = {}
    referer = "http://abit.donntu.org/"   
    url = "http://abit.donntu.org/data/get_spec.php?"\
          "id_vid_podgot={education_level_id}&kod_fo_dec={form_id}&"\
          "kod_ft={faculty_id}&kurs=-1".format(education_level_id=education_level_id,
                                               form_id=form_id,
                                               faculty_id=faculty_id)
    specs_dict = get_json(url, referer)
    return specs_dict

def write_specs_by_faculty():
    """
    Записать все специальности по факультетам в файл.
    Функция требует наличия файла helpers_yyyy-mm-dd.json
    Функция создат такие файлы:
        - specs_by_faculty_yyyy-mm-dd.json - (Все специальности по факультетам в одном файле)
        - фкнт_yyyy-mm-dd.json - Все специальности всех форм обучения факультета КНТ
        - и т. д. по всем факультетам
    """
    helpers = read_json(get_file_name("helpers"))
    
    specs_by_faculty = OrderedDict()
    for i in helpers["faculties"]:
        id = i["id"]
        name = i["name"]
        r = re.search('\((\w+)\) ([-\w ]+)', name)
        if not (r and r.group(1) and r.group(2)):
            continue
        abbr = r.group(1).strip()
        name = r.group(2).strip()
        
        specs = []
        for education_level in helpers["education_levels"]:
            specs.extend(specs_dumps(education_level_id=education_level["id"], faculty_id=id))
            time.sleep(random.random())
        
        specs_by_faculty[name] = specs
                
        write_json(get_file_name(abbr.lower()), {"name": name, "abbr": abbr, "specs": specs})
        
    write_json(get_file_name("specs_by_faculty"), specs_by_faculty)

def search_by_photoid_dumps(start_id, end_id):
    abiturients = {}
    abits = OrderedDict()
    abiturients["photoid"] = abits
    referer = "http://abit.donntu.org/photoF.html"
    url = "http://abit.donntu.org/data/abit_search.php?id_photo={photoid}&second_name=-1"
    for id in range(start_id, end_id):
        info = get_json(url.format(photoid=id), referer)
        time.sleep(random.random())
        print("Loading: {}/{}".format(id, end_id), end="\r")
        if len(info) == 0:
            continue
        abits[id] = info
    write_json(get_file_name("abiturients"), abiturients)
    
    
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        write_helpers()
        write_specs_by_faculty()
    
    if len(sys.argv) > 3 and sys.argv[1] == "dump_abit" \
       and int(sys.argv[2]) and int(sys.argv[3]):
        search_by_photoid_dumps(int(sys.argv[2]), int(sys.argv[3]) + 1)
        
    if len(sys.argv) == 1:
        print("Use: $ python abit_donntu.py dump - get faculties and other")
        print("Use: $ python abit_donntu.py dump_abit <start_id> <end_id> - get abiturients\n")


if __name__ == '__main__':
    main()