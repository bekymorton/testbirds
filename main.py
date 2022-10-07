import telebot as tb
from telebot import types
import requests as rq
import random as rd
import os



obj_url = os.environ['OBJ_URL']
wikiEndPoint = os.environ['WIKIENDPOINT']
password = os.environ['PASSWORD']
username = os.environ['USERNAME']
bot_token = os.environ['BOT_TOKEN']


class Obj:
    def __init__(self, obj_spec, objName_ru, soundUrl, objDescr, objViewUrl):
        self.soundsUrl = []  # перечень песен представителя фауны
        self.addSound(soundUrl)
        self.obj_spec = ''  # латинское название вида представителя фауны. Состоит из нескольких слов
        self.setObjSpec(obj_spec)  # сохранение вида представителя фауны
        self.objViewUrl = ''  # URL фотографии представителя фауны
        self.setObjViewUrl(objViewUrl)
        self.objName_ru = ''  # русское наименование представителя фауны
        self.setObjName_ru(objName_ru)
        self.objDescr = ''  # Краткое описание представителя фауны
        self.setObjDescr(objDescr)

    # Задает видовое название представителя фауны в виде словаря для REST запроса
    def setObjSpec(self, obj_spec):
        self.obj_spec = obj_spec

    # задает русское наименование представителя фауны
    def setObjName_ru(self, objName_ru):
        self.objName_ru = objName_ru

    # Возвращает русское наименование представителя фауны
    def getObjName_ru(self):
        return self.objName_ru

    # задает URL фотографии представителя фауны
    def setObjViewUrl(self, objViewUrl):
        self.objViewUrl = objViewUrl

    # Возвращает URL фотографии представителя фауны
    def getObjViewUrl(self):
        return self.objViewUrl

    # задает URL краткого описания представителя фауны
    def setObjDescr(self, objDescr):
        self.objDescr = objDescr

    # Возвращает URL краткого описания представителя фауны
    def getObjDescr(self):
        return self.objDescr

    # добавляет очередную песню в список песен представителя фауны
    def addSound(self, sndUrl):
        self.soundsUrl.append(sndUrl)

    # возвращает песню представителя фауны выбранную случайным
    # образом из имеющихся для этого представителя фауны песен
    def getObjSongUrl(self):
        return self.soundsUrl[rd.randint(0, len(self.soundsUrl) - 1)]


class WikiREST_API:
    def __init__(self, wikiEndPoint):
        self.wikiUrl = wikiEndPoint  # Конечная точка для wiki
        self.errGet = {}  # словарь ошибок при выполнении запроса
        self.json = {}  # полученные данные запроса в формате json

    # возвращает информацию в формате json для заданного словаря параметров params,
    # {'gen':..., 'sp'...}
    def getQueryData(self, params):
        resp = rq.get(self.wikiUrl + 'summary/' + params)
        if resp.status_code == 200:
            # Запрос выполнен успешно
            self.json = resp.json()  # полученные json данные запроса
            return True
        else:
            self.errGet[params] = str(resp.status_code)
            return False

    # возвращает русское наименование выбранного объекта
    def getObjName_ru(self):
        return self.json['title']

    # возвращает ссылку на краткое описание объекта
    def getObjDescr(self):
        return self.json['extract']

    # возвращает ссылку на фотографию объекта
    def getObjPhotoUrl(self):
        return self.json['thumbnail']['source']


class ObjREST_API:
    def __init__(self, user, psw, endPoint, wikiEndPoint, qtyObj=5):
        self.params = {"page": 1}  # настраиваемые параметры запроса для сайта птиц
        self.user = user  # Пользователь для сайта птиц
        self.psw = psw  # Пароль пользователя для сайта птиц
        self.url = endPoint  # Конечная точка для сайта птиц
        self.page = 1  # Стартовая страница запроса для сайта птиц
        self.numPages = 0  # количество страниц ответа на запрос для сайта птиц
        self.qtyObj = qtyObj  # количество птиц для викторины
        self.obj = {}  # данные о птицах в виде словаря: objName_ru : objInstance
        self.errGet = {}  # словарь ошибок при выполнении запроса по страницам
        self.recObj = {}  # словарь записей страницы птиц
        self.objNamesForRandom = []  # Список имен птиц для случайной выборки
        self.wikiObj = WikiREST_API(wikiEndPoint)  # объект REST API для wiki
        self.wikiParams = ''  # видовое описание объекта для запроса из wiki
        self.Lic = 'Запись звука  получена с сайта https://xeno-canto.org/ на условиях Creative Common Licenses.'

    # возвращает № страницы, выбранной случайным образом из имеющихся в запросе
    def getRandomPage(self):
        return rd.randint(1, self.numPages)

    # возвращает выборку одной страницы ответа на запрос в json формате и количество страниц ответа на запрос
    def getDataObj(self, page=1):
        # Получаем данные с сайта
        params = {}
        params["page"] = page
        resp = rq.get(self.url, params=self.params, auth=(self.user, self.psw), allow_redirects=True)
        if resp.status_code == 200:
            # Запрос выполнен успешно
            json = resp.json()  # полученные json данные запроса заданной страницы
            self.numPages = json["numPages"]  # Количество страниц в запросе
            self.recObj.clear()  # предварительная очистка словаря записей птиц страницы
            self.recObj = json['recordings']
            return True
        else:
            self.errGet[page] = str(resp.status_code)
            return False

    # заполение списка объектов для викторины случайным образом
    def getRandomLstObj(self):
        if self.getDataObj(self.page) == False:
            # ошибка выполнения запроса
            return False
        # ответ получен
        while len(self.obj) < self.qtyObj:
            # пока не занесено требуемое количество птиц
            # выбор случайной записи страницы
            record = self.recObj[rd.randint(0, len(self.recObj) - 1)]
            # Выборка описания объекта
            self.wikiParams = record['gen'] + ' ' + record['sp']
            # Выполнение запроса на wiki
            if self.wikiObj.getQueryData(self.wikiParams) == False:
                # ошибка выполнения запроса
                return False
            # Запрос выполнен успешно
            # создание экземпляра объекта
            objName_ru = self.wikiObj.getObjName_ru()
            if objName_ru not in self.obj:
                # Выбранная птица еще не занесена в список викторины
                self.obj[objName_ru] = Obj(self.wikiParams, objName_ru, record['file'], self.wikiObj.getObjDescr(),
                                           self.wikiObj.getObjPhotoUrl())
                self.objNamesForRandom.append(objName_ru)
            self.page = self.getRandomPage()  # Выбор очередной страницы
            if self.getDataObj(self.page) == False:
                # ошибка выполнения запроса
                return False
        return True

    # возвращает список объектов, выбранных для викторины
    def getObjList(self):
        return self.obj

    # возвращает список ошибок выполнения запросов страниц
    # в формате {page: 'код ошибки: ....'}
    def getErrors(self):
        return self.errGet

    # Возвращает список имен объектов для случайной выборки
    def getObjNamesForRandom(self):
        return self.objNamesForRandom


LstObj = {}  # Словарь выбранных обектов в формате {Имя объекта : Объект класса Obj}
objNames = []  # Список имен выбранный объектов для рандомизации
tstObj = isinstance  # класс случайно выбранного объекта для угадывания

bot = tb.TeleBot(bot_token)  # Создание экземпляра класса TeleBot
objGetData = ObjREST_API(username, password, obj_url, wikiEndPoint)
if objGetData.getRandomLstObj() == True:
    LstObj = objGetData.getObjList()
    objNames = objGetData.getObjNamesForRandom()
    tstObj = LstObj[objNames[0]]
    menuLevel = 0
    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    info_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)


# Регистрация функции в качестве обработчика команды /start
@bot.message_handler(commands=['start'])
def start(message):
    global LstObj, objNames, tstObj, menuLevel, main_markup, info_markup
    bot.send_message(message.chat.id, 'Минуточку...')
    objGetData = ObjREST_API(username, password, obj_url, wikiEndPoint)
    if objGetData.getRandomLstObj() == True:
        LstObj.clear()
        LstObj = objGetData.getObjList()
        objNames = objGetData.getObjNamesForRandom()
        tstObj = LstObj[objNames[rd.randint(0, len(objNames) - 1)]]
        btn1 = types.KeyboardButton('Информация')
        btn2 = types.KeyboardButton('Следующий раунд')
        btn3 = types.KeyboardButton(LstObj[objNames[0]].getObjName_ru())
        btn4 = types.KeyboardButton(LstObj[objNames[1]].getObjName_ru())
        btn5 = types.KeyboardButton(LstObj[objNames[2]].getObjName_ru())
        btn6 = types.KeyboardButton(LstObj[objNames[3]].getObjName_ru())
        btn7 = types.KeyboardButton(LstObj[objNames[4]].getObjName_ru())
        main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        main_markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
        btn8 = types.KeyboardButton('В главное меню')
        btn9 = types.KeyboardButton(LstObj[objNames[0]].getObjName_ru())
        btn10 = types.KeyboardButton(LstObj[objNames[1]].getObjName_ru())
        btn11 = types.KeyboardButton(LstObj[objNames[2]].getObjName_ru())
        btn12 = types.KeyboardButton(LstObj[objNames[3]].getObjName_ru())
        btn13 = types.KeyboardButton(LstObj[objNames[4]].getObjName_ru())
        info_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        info_markup.add(btn8, btn9, btn10, btn11, btn12, btn13)

        bot.send_message(message.chat.id, 'Прослушайте песню и угадайте по ней представителя Фауны...')
        bot.send_audio(message.chat.id, tstObj.getObjSongUrl(), caption=objGetData.Lic, reply_markup=main_markup)
    else:
        bot.send_message(message.chat.id, 'При выборке данных зафиксирована ошибка...')


@bot.message_handler(content_types=['text'])
def button_handler(message):
    global LstObj, objNames, tstObj, menuLevel, main_markup, info_markup
    if (message.text == LstObj[objNames[0]].getObjName_ru()):
        if menuLevel == 0:
            if LstObj[objNames[0]].getObjName_ru() == tstObj.getObjName_ru():
                bot.send_message(message.chat.id, text="Вы угадали!")
            else:
                bot.send_message(message.chat.id, text="Попробуйте еще раз...")
        else:
            bot.send_photo(message.chat.id, LstObj[objNames[0]].getObjViewUrl())
            bot.send_message(message.chat.id, LstObj[objNames[0]].getObjDescr())
            bot.send_audio(message.chat.id, LstObj[objNames[0]].getObjSongUrl(), caption=objGetData.Lic,
                           reply_markup=info_markup)
    elif (message.text == LstObj[objNames[1]].getObjName_ru()):
        if menuLevel == 0:
            if LstObj[objNames[1]].getObjName_ru() == tstObj.getObjName_ru():
                bot.send_message(message.chat.id, text="Вы угадали!")
            else:
                bot.send_message(message.chat.id, text="Попробуйте еще раз...")
        else:
            bot.send_photo(message.chat.id, LstObj[objNames[1]].getObjViewUrl())
            bot.send_message(message.chat.id, LstObj[objNames[1]].getObjDescr())
            bot.send_audio(message.chat.id, LstObj[objNames[1]].getObjSongUrl(), caption=objGetData.Lic,
                           reply_markup=info_markup)
    elif (message.text == LstObj[objNames[2]].getObjName_ru()):
        if menuLevel == 0:
            if LstObj[objNames[2]].getObjName_ru() == tstObj.getObjName_ru():
                bot.send_message(message.chat.id, text="Вы угадали!")
            else:
                bot.send_message(message.chat.id, text="Попробуйте еще раз...")
        else:
            bot.send_photo(message.chat.id, LstObj[objNames[2]].getObjViewUrl())
            bot.send_message(message.chat.id, LstObj[objNames[2]].getObjDescr())
            bot.send_audio(message.chat.id, LstObj[objNames[2]].getObjSongUrl(), caption=objGetData.Lic,
                           reply_markup=info_markup)
    elif (message.text == LstObj[objNames[3]].getObjName_ru()):
        if menuLevel == 0:
            if LstObj[objNames[3]].getObjName_ru() == tstObj.getObjName_ru():
                bot.send_message(message.chat.id, text="Вы угадали!")
            else:
                bot.send_message(message.chat.id, text="Попробуйте еще раз...")
        else:
            bot.send_photo(message.chat.id, LstObj[objNames[3]].getObjViewUrl())
            bot.send_message(message.chat.id, LstObj[objNames[3]].getObjDescr())
            bot.send_audio(message.chat.id, LstObj[objNames[3]].getObjSongUrl(), caption=objGetData.Lic,
                           reply_markup=info_markup)
    elif (message.text == LstObj[objNames[4]].getObjName_ru()):
        if menuLevel == 0:
            if LstObj[objNames[4]].getObjName_ru() == tstObj.getObjName_ru():
                bot.send_message(message.chat.id, text="Вы угадали!")
            else:
                bot.send_message(message.chat.id, text="Попробуйте еще раз...")
        else:
            bot.send_photo(message.chat.id, LstObj[objNames[4]].getObjViewUrl())
            bot.send_message(message.chat.id, LstObj[objNames[4]].getObjDescr())
            bot.send_audio(message.chat.id, LstObj[objNames[4]].getObjSongUrl(), caption=objGetData.Lic,
                           reply_markup=info_markup)
    elif (message.text == 'Информация'):
        menuLevel = 1
        bot.send_message(message.chat.id, 'Выберите интересующего представителя фауны', reply_markup=info_markup)
    elif (message.text == 'В главное меню'):
        menuLevel = 0
        bot.send_audio(message.chat.id, tstObj.getObjSongUrl(), reply_markup=main_markup)
    elif (message.text == 'Следующий раунд'):
        bot.send_message(message.chat.id, 'Следующий раунд!', reply_markup=types.ReplyKeyboardRemove())
        start(message)


# Постоянная отправка запроса на сервера Telegram (none_stop - не будет останавливаться даже
# в случае получения ошибки)
bot.polling(none_stop=True)
