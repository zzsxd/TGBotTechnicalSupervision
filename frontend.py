from telebot import types


class Bot_inline_btns:
    def __init__(self):
        super(Bot_inline_btns, self).__init__()
        self.__markup = types.InlineKeyboardMarkup(row_width=1)

    def start_buttons(self):
        one = types.InlineKeyboardButton('💫 Подписаться на канал', url="https://t.me/ShuGuDuLashes")
        two = types.InlineKeyboardButton('📞 Поделиться номером', callback_data="share_contact")
        self.__markup.add(one, two)
        return self.__markup
    
    def yes_no_buttons(self):
        markup = types.InlineKeyboardMarkup(row_width=2)
        yes_btn = types.InlineKeyboardButton('✅ Да', callback_data="answer_yes")
        no_btn = types.InlineKeyboardButton('❌ Нет', callback_data="answer_no")
        markup.add(yes_btn, no_btn)
        return markup
    
    def restart_button(self):
        markup = types.InlineKeyboardMarkup(row_width=1)
        restart_btn = types.InlineKeyboardButton('🔄 Начать новый аудит', callback_data="restart_audit")
        markup.add(restart_btn)
        return markup