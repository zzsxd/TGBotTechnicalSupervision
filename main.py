# main.py
import time
import telebot
import os
import re
import json
import threading
import platform
from telebot import types
from threading import Lock
from config_parser import ConfigParser
from frontend import Bot_inline_btns
from backend import DbAct
from db import DB

config_name = 'secrets.json'

AUDIT_CHECKLIST = [
    {
        "section": "1. Оклейка входной двери",
        "questions": [
            {"id": "q1_1", "text": "Контур двери заклеен двухсторонним скотчем?"},
            {"id": "q1_2", "text": "Полотно оклеено ударопрочным материалом?"},
            {"id": "q1_3", "text": "Снаружи наклеен логотип компании?"},
            {"id": "q1_4", "text": "Внутри размещены правила компании?"},
            {"id": "q1_5", "text": "Установлен временный сейф для хранения ключей?"},
            {"id": "q1_6", "text": "Влажная тряпка на входе?"},
            {"id": "q1_7", "text": "Временный унитаз установлен?"},
            {"id": "q1_8", "text": "Временный доступ к воде?"},
        ]
    },
    {
        "section": "2. Окна и подоконники",
        "questions": [
            {"id": "q2_1", "text": "Окна заклеены плёнкой?"},
            {"id": "q2_2", "text": "Подоконники защищены ударостойким материалом?"},
            {"id": "q2_3", "text": "Радиаторы укрыты полностью и качественно?"},
        ]
    },
    {
        "section": "3. Инфраструктура объекта",
        "questions": [
            {"id": "q3_1", "text": "Есть раздевалка?"},
            {"id": "q3_2", "text": "Аптечка присутствует?"},
            {"id": "q3_3", "text": "Есть бокс/кейс для документов/материалов?"},
            {"id": "q3_4", "text": "В каждой комнате при наличии — размещён лист с дизайн-проектом на стене?"},
        ]
    },
    {
        "section": "4. Чистовые материалы",
        "questions": [
            {"id": "q4_1", "text": "Аккуратно сложены?"},
            {"id": "q4_2", "text": "Укрыты защитным материалом (смонтированные и не смонтированные)?"},
        ]
    },
    {
        "section": "5. Черновые материалы",
        "questions": [
            {"id": "q5_1", "text": "Сложены в отведённом месте?"},
            {"id": "q5_2", "text": "Находятся в чистом виде, без пыли и грязи?"},
        ]
    },
    {
        "section": "6. Бытовой мусор",
        "questions": [
            {"id": "q6_1", "text": "На объекте нет разбросанного мусора?"},
        ]
    },
    {
        "section": "7. Порядок после работ",
        "questions": [
            {"id": "q7_1", "text": "Наведён порядок после последнего этапа работ?"},
            {"id": "q7_2", "text": "На объекте нет запаха сигарет?"},
        ]
    }
]

def calculate_score(answers):
    total_questions = sum(len(section["questions"]) for section in AUDIT_CHECKLIST)
    positive_answers = sum(1 for answer in answers.values() if answer)
    return positive_answers, total_questions

def get_result_message(score, total):
    if score >= 20:
        return "Отлично"
    elif score >= 16:
        return "Хорошо"
    elif score >= 14:
        return "Удовлетворительно"
    else:
        return "Требуется немедленное исправление"

def main():
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        buttons = Bot_inline_btns()
        db_actions.add_user(user_id, message.from_user.first_name, 
                        message.from_user.last_name, 
                        f'@{message.from_user.username}')
        db_actions.clear_audit_data(user_id)
        db_actions.set_user_system_key(user_id, "user_object", None)
        
        bot.send_message(
            user_id, 
            'Привет! Проведём аудит объекта по чек-листу чистоты. Отвечай «Да» или «Нет» — начнём?\n'
            'Введите номер объекта для начала 😊',
            parse_mode='HTML'
        )

    @bot.message_handler(content_types=['text'])
    def text_message(message):
        user_id = message.chat.id
        user_input = message.text.strip()
        if not db_actions.user_is_existed(user_id):
            return
        
        current_section = db_actions.get_user_system_key(user_id, "current_section")
        current_question = db_actions.get_user_system_key(user_id, "current_question")
        
        if current_section == 0 and current_question == 0 and db_actions.get_user_system_key(user_id, "user_object") is None:
            if not user_input:
                bot.send_message(user_id, "Пожалуйста, введите номер объекта.")
                return
                
            db_actions.set_user_system_key(user_id, "user_object", user_input)
            ask_question(user_id, 0, 0)

    def ask_question(user_id, section_idx, question_idx):
        section = AUDIT_CHECKLIST[section_idx]
        question = section["questions"][question_idx]
        
        buttons = Bot_inline_btns()
        bot.send_message(
            user_id,
            f"{section['section']}\n\n•{question['text']}",
            reply_markup=buttons.yes_no_buttons()
        )

    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        user_id = call.message.chat.id
        buttons = Bot_inline_btns()
        
        if call.data in ["answer_yes", "answer_no"]:
            current_section = db_actions.get_user_system_key(user_id, "current_section")
            current_question = db_actions.get_user_system_key(user_id, "current_question")
            
            if current_section is None or current_question is None:
                bot.send_message(user_id, "Пожалуйста, начните аудит с команды /start")
                return
                
            try:
                section = AUDIT_CHECKLIST[current_section]
                question = section["questions"][current_question]
                
                answer = call.data == "answer_yes"
                db_actions.add_audit_answer(user_id, question["id"], answer)
            
            
            
                next_question = current_question + 1
                next_section = current_section
                
                if next_question >= len(section["questions"]):
                    next_question = 0
                    next_section += 1
                    
                    if next_section >= len(AUDIT_CHECKLIST):
                        answers = db_actions.get_audit_results(user_id)
                        score, total = calculate_score(answers)
                        result = get_result_message(score, total)
                        
                        object_number = db_actions.get_user_system_key(user_id, "user_object")
                        report_message = (
                            f"📋 Результат аудита объекта {object_number}:\n\n"
                            f"• Всего баллов: {score} из {total}\n"
                            f"• Оценка: {result}\n\n"
                        )
                        
                        if score == total:
                            report_message += "🎉 Поздравляем! Объект в идеальном состоянии!"
                        elif score >= 16:
                            report_message += "👉 Рекомендую устранить мелкие замечания до следующей проверки."
                        elif score >= 14:
                            report_message += "⚠️ Требуется внимание к некоторым аспектам объекта."
                        else:
                            report_message += "🚨 Требуется немедленное исправление недостатков!"
                        
                        bot.send_message(
                            user_id,
                            report_message,
                            reply_markup=buttons.restart_button()
                        )
                        return
                db_actions.set_user_system_key(user_id, "current_section", next_section)
                db_actions.set_user_system_key(user_id, "current_question", next_question)
                ask_question(user_id, next_section, next_question)
            except Exception as e:
                bot.send_message(user_id, "Ошибка")
            
        elif call.data == "restart_audit":
            db_actions.clear_audit_data(user_id)
            db_actions.set_user_system_key(user_id, "current_question", 0)
            db_actions.set_user_system_key(user_id, "current_section", 0)
            bot.send_message(
                user_id,
                'Введите номер объекта для нового аудита 😊',
                parse_mode='HTML'
            )

    bot.polling(none_stop=True)

if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config)
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()