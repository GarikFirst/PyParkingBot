from argparse import ArgumentParser
from json import dump, load
from logging import INFO, basicConfig, getLogger

from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, PicklePersistence, Updater)

from structures.parking import Parking as Parking
from structures.stats import Stats as Stats
from structures.user_view import UserView as UserView


def start(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        manage_user(update, context)
        parking = context.bot_data['parking']
        markup = make_keyboard(context, str(update.effective_user.id))
        info = update.effective_message.reply_text('---')
        status = update.effective_message.reply_text(
            parking.state_text, reply_markup=markup, parse_mode='MarkdownV2')
        view = UserView(info, status)
        context.bot_data['views'][str(update.effective_user.id)] = view


def stop(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        try:
            view = context.bot_data['views'][str(update.effective_user.id)]
            view.delete()
            manage_user(update, context, False)
        except KeyError:
            pass


def parking_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        update.callback_query.edit_message_text('test')
        context.user_data['is_in_menu'] = False
        number = update.callback_query.data
        parking = context.bot_data['parking']
        try:
            stats = context.bot_data['stats']
            for place in parking.places:
                if place.number == number:
                    stats.count(place)
                    place.toggle_state(str(update.effective_user.id))
                    state = place.state
            if state == 'reserved':
                action_text = 'зарервировал'
            elif state == 'occupied':
                action_text = 'занял'
            elif state == 'free':
                action_text = 'освободил'
            update.callback_query.answer(f'Вы {action_text}и место {number}')
            action = ' '.join([
                '*' + users[str(update.effective_user.id)] + '*', action_text,
                'место', '*' + number + '*'])
            update_state(update, context, action)
        except ValueError:
            update.callback_query.answer(f'Место {number} не свободно!')


def cancel_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        context.user_data['is_in_menu'] = False
        number = update.callback_query.data.split('.')[1]
        parking = context.bot_data['parking']
        try:
            for place in parking.places:
                if place.number == number:
                    place.cancel_reserve()
            update.callback_query.answer(f'Вы отменили резерв места {number}')
            action = ' '.join([
                '*' + users[str(update.effective_user.id)] + '*',
                'отменил резерв места', '*' + number + '*'])
            update_state(update, context, action)
        except ValueError:
            update.callback_query.answer(f'Место {number} не ваше!')


def clear_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        context.user_data['is_in_menu'] = False
        update.callback_query.answer('Вы выбрали очистку парковки')
        parking = context.bot_data['parking']
        places = parking.clear()
        if places:
            stats = context.bot_data['stats']
            for place in places:
                stats.count(place)
        action = ' '.join(['*' + users[str(update.effective_user.id)] + '*',
                           'очистил парковочное пространство'])
        update_state(update, context, action)


def statistics_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        context.user_data['is_in_menu'] = context.user_data.get('is_in_menu',
                                                                False)
        if not context.user_data['is_in_menu']:
            update.callback_query.answer('Вы открыли статистику')
            context.user_data['is_in_menu'] = True
            stats = context.bot_data['stats']
            update_state(update, context, stats.message_text, True)
        else:
            update.callback_query.answer('Вы закрыли статистику')
            context.user_data['is_in_menu'] = False
            update_state(update, context, r'\-\-\-', True)


def update_state(update: Update, context: CallbackContext, info: str,
                 personal=False) -> None:
    try:
        if personal:
            view = context.bot_data['views'][str(update.effective_user.id)]
            view.update(info, None)
        else:
            for user in users:
                parking = context.bot_data['parking']
                view = context.bot_data['views'][user]
                markup = make_keyboard(context, user)
                view.update(info, parking.state_text, markup)
    except BadRequest:
        # If user delete original message - just send new and save the new view
        info = update.effective_message.reply_text('---')
        status = update.effective_message.reply_text(
            parking.state_text, reply_markup=markup, parse_mode='MarkdownV2')
        view = UserView(info, status)
        context.bot_data['views'][str(update.effective_user.id)] = view


def make_keyboard(context: CallbackContext,
                  user_id: str) -> InlineKeyboardMarkup:
    keyboard = []
    parking = context.bot_data['parking']
    for place in parking.state:
        place_sign, state, number, occupant = place
        if occupant is not None:
            person = users[str(occupant)]
        else:
            person = 'место свободно'
        caption = ' '.join([place_sign, number, person])
        place_button = InlineKeyboardButton(caption, callback_data=number)
        cancel_button = InlineKeyboardButton(' '.join(
            [emojize(':right_arrow_curving_left:'), 'Отменить резерв']),
            callback_data=''.join(['cancel.', number]))
        clear_button = InlineKeyboardButton(' '.join(
            [emojize(':FREE_button:'), 'Очистить парковку']),
            callback_data='clear')
        statistics_button = InlineKeyboardButton(' '.join(
            [emojize(':bar_chart:'), 'Статистика']),
            callback_data='statistics')
        if state == 'reserved' and occupant == user_id:
            keyrow = []
            keyrow.append(place_button)
            keyrow.append(cancel_button)
            keyboard.append(keyrow)
        else:
            keyboard.append([place_button])
    if not parking.is_free:
        keyrow = []
        keyrow.append(clear_button)
        keyrow.append(statistics_button)
        keyboard.append(keyrow)
    else:
        keyboard.append([statistics_button])
    return InlineKeyboardMarkup(keyboard)


def manage_user(update: Update, context: CallbackContext, check=True) -> None:
    user_id = str(update.effective_user.id)
    if check:
        if update.effective_user.full_name is None:
            username = update.effective_user.username
        else:
            username = update.effective_user.full_name
        if user_id not in users or users[user_id] != username:
            users[user_id] = username
        save_json(config['users_file'], users)
    elif not check and user_id in users:
        context.bot_data['views'].pop(user_id, None)
        users.pop(user_id, None)
        save_json(config['users_file'], users)


def log_event(update: Update, action: str) -> None:
    logger.log(INFO, f'{users[str(update.effective_user.id)]} - {action}')


def load_json(filename) -> object:
    try:
        with open(filename) as file:
            data = load(file)
        return data
    except FileNotFoundError:
        exit(f'File "{filename}" does not exist')


def save_json(filename, data) -> None:
    with open(filename, 'w') as file:
        dump(data, file, indent=4, sort_keys=True)


def get_config() -> dict:
    parser = ArgumentParser(
        prog='Logrocon Parking Bot v.3')
    parser.add_argument('-c', '--config',  default='config.json', metavar='C',
                        help='config file name')
    args = vars(parser.parse_args())
    config = load_json(args['config'])
    return config


config = get_config()
users = load_json(config['users_file'])

log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
basicConfig(filename=config['log_file'], format=log_format, level=INFO)
logger = getLogger(__name__)

handlers = [CommandHandler('start', start),
            CommandHandler('stop', stop),
            CallbackQueryHandler(cancel_handler, pattern='cancel.*'),
            CallbackQueryHandler(clear_handler, pattern='clear'),
            CallbackQueryHandler(statistics_handler, pattern='statistics'),
            CallbackQueryHandler(parking_handler)]


def main():
    updater = Updater(token=config['token'], persistence=PicklePersistence(
        filename=config['data_file'], store_chat_data=False, on_flush=False))
    dispatcher = updater.dispatcher
    dispatcher.bot_data['stats'] = dispatcher.bot_data.get('stats',
                                                           Stats(users))
    dispatcher.bot_data['views'] = dispatcher.bot_data.get('views', {})
    dispatcher.bot_data['parking'] = dispatcher.bot_data.get(
        'parking', Parking(config['places']))
    if ([x[2] for x in dispatcher.bot_data['parking'].state]
       != config['places']):
        dispatcher.bot_data['parking'] = Parking(config['places'])
    for handler in handlers:
        dispatcher.add_handler(handler)
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == '__main__':
    main()
