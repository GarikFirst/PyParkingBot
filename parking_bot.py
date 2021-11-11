from argparse import ArgumentParser
from json import dump, load
from logging import INFO, basicConfig, getLogger
from subprocess import run

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
        log_event(update, 'Отправил start')


def stop(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        try:
            log_event(update, 'Отправил stop')
            view = context.bot_data['views'][str(update.effective_user.id)]
            view.delete()
            update.effective_message.reply_text(
                'Вы перестали получать уведомления. Вы можете в любой момент' +
                ' вернутся к их получению командой /start.')
            manage_user(update, context, False)
        except KeyError:
            log_event(update, 'Отправил stop повторно')


def parking_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        manage_user(update, context)
        context.user_data['is_in_menu'] = False
        number = update.callback_query.data
        try:
            parking = context.bot_data['parking']
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
            action = (f'*{users[str(update.effective_user.id)]}* ' +
                      f'{action_text} место *{number}*')
            update_state(update, context, action)
            log_event(update, action)
        except ValueError:
            update.callback_query.answer(f'Место {number} не свободно!')
            log_event(update, f'Нажал на несвободное место {number}')


def cancel_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        manage_user(update, context)
        context.user_data['is_in_menu'] = False
        number = update.callback_query.data.split('.')[1]
        parking = context.bot_data['parking']
        try:
            for place in parking.places:
                if place.number == number:
                    place.cancel_reserve(str(update.effective_user.id))
            update.callback_query.answer(f'Вы отменили резерв места {number}')
            action = (f'*{users[str(update.effective_user.id)]}* ' +
                      f'отменил резерв места *{number}*')
            update_state(update, context, action)
            log_event(update, action)
        except ValueError:
            update.callback_query.answer(
                'Используйте клавиатуру из последнего сообщения!')
            log_event(update, 'Пытался отменить резерв на старой клавиатуре')


def clear_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        manage_user(update, context)
        context.user_data['is_in_menu'] = False
        try:
            parking = context.bot_data['parking']
            places = parking.clear()
            if places:
                stats = context.bot_data['stats']
                for place in places:
                    stats.count(place)
            update.callback_query.answer('Вы выбрали очистку парковки')
            action = (f'*{users[str(update.effective_user.id)]}* ' +
                      'очистил парковочное пространство')
            update_state(update, context, action)
            log_event(update, action)
        except ValueError:
            update.callback_query.answer(
                'Используйте клавиатуру из последнего сообщения!')
            log_event(update, 'Пытался очистить парковку на старой клавиатуре')


def statistics_handler(update: Update, context: CallbackContext) -> None:
    if (config['whitelist'] and str(update.effective_user.id) in users
       or not config['whitelist']):
        manage_user(update, context)
        context.user_data['is_in_menu'] = context.user_data.get('is_in_menu',
                                                                False)
        if not context.user_data['is_in_menu']:
            update.callback_query.answer('Вы открыли статистику')
            context.user_data['is_in_menu'] = True
            stats = context.bot_data['stats']
            update_state(update, context, stats.message_text, True)
            log_event(update, 'Открыл статистику')
        else:
            update.callback_query.answer('Вы закрыли статистику')
            context.user_data['is_in_menu'] = False
            update_state(update, context, r'\-\-\-', True)
            log_event(update, 'Закрыл статистику')


def update_state(update: Update, context: CallbackContext, info: str,
                 personal=False) -> None:
    """ Personal or bulk messages update """
    def bad_request(user, text=None) -> None:
        """ Resend messages if user messed them up """
        log_event(update, f'{users[user]} что-то сделал с сообщениями бота')
        markup = make_keyboard(context, user)
        if text is not None:
            info = update.effective_message.bot.send_message(
                user, text, parse_mode='MarkdownV2')
        else:
            info = update.effective_message.bot.send_message(user, '---')
        status = update.effective_message.bot.send_message(
            user, parking.state_text, reply_markup=markup,
            parse_mode='MarkdownV2')
        view = UserView(info, status)
        context.bot_data['views'][user] = view
        log_event(update, f'Отправили уведомление {users[user]}')

    parking = context.bot_data['parking']
    if personal:
        try:
            view = context.bot_data['views'][str(update.effective_user.id)]
            view.update(info, None)
        except BadRequest:
            bad_request(str(update.effective_user.id))
    else:
        for user in users:
            try:
                view = context.bot_data['views'][user]
                markup = make_keyboard(context, user)
                view.update(info, parking.state_text, markup)
                log_event(update, f'Отправили уведомление {users[user]}')
            except BadRequest:
                bad_request(user, info)


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
        # Replace for telegram markdown v2
        for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>',
                   '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            username = username.replace(ch, '')
        if user_id not in users or users[user_id] != username:
            users[user_id] = username
            save_json(config['users_file'], users)
            stats = context.bot_data['stats']
            stats.update_users(users)
            log_event(update, 'Добавили пользователя')
    elif not check and user_id in users:
        context.bot_data['views'].pop(user_id, None)
        users.pop(user_id, None)
        save_json(config['users_file'], users)
        log_event(update, 'Удалили пользователя')


def log_event(update: Update, action: str) -> None:
    try:
        username = f'{users[str(update.effective_user.id)]}'
    except KeyError:
        username = update.effective_user.username
    action = action.replace('*', '')
    logger.log(INFO, f'{username} - {action}')


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


def toggle_whitelist(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == config['owner_id']:
        config['whitelist'] = not config['whitelist']
        update.effective_message.reply_text('Whitelist mode: ' +
                                            f'{config["whitelist"]}')
        log_event(update, 'Переключил режим whitelist на ' +
                  f'{config["whitelist"]}')
    else:
        log_event(update, 'Отправил whitelist, хотя не должен о ней знать')


def get_logs(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == config['owner_id']:
        if not context.args:
            length = config['logging']['log_length']
            log_event(update, f'Отправил logs без ключей, берем {length}')
        else:
            length = context.args[0]
            log_event(update, f'Отправил logs с ключем {length}')
        result = run(['tail', '-n', length, config['logging']['log_file']],
                     capture_output=True, universal_newlines=True)
        log = result.stdout
        if len(log) > 4096:
            for x in range(0, len(log), 4096):
                update.effective_message.reply_text(log[x:x+4096])
        else:
            update.effective_message.reply_text(log)
    else:
        log_event(update, 'Отправил logs, хотя не должен о ней знать')


config = get_config()
users = load_json(config['users_file'])

log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
basicConfig(filename=config['logging']['log_file'],
            format=log_format, level=INFO)
logger = getLogger(__name__)

handlers = [CommandHandler('start', start),
            CommandHandler('stop', stop),
            CallbackQueryHandler(cancel_handler, pattern='cancel.*'),
            CallbackQueryHandler(clear_handler, pattern='clear'),
            CallbackQueryHandler(statistics_handler, pattern='statistics'),
            CallbackQueryHandler(parking_handler),
            CommandHandler('whitelist', toggle_whitelist),
            CommandHandler('logs', get_logs, pass_args=True)]


def main():
    updater = Updater(token=config['token'], persistence=PicklePersistence(
        filename=config['data_file_prefix'], store_chat_data=False,
        single_file=False, on_flush=False))
    dispatcher = updater.dispatcher
    dispatcher.bot_data['stats'] = dispatcher.bot_data.get('stats',
                                                           Stats(users))
    dispatcher.bot_data['views'] = dispatcher.bot_data.get('views', {})
    dispatcher.bot_data['parking'] = dispatcher.bot_data.get(
        'parking', Parking(config['places']))
    # Create new parking if places in config changed
    if ([x[2] for x in dispatcher.bot_data['parking'].state]
       != config['places']):
        dispatcher.bot_data['parking'] = Parking(config['places'])
    for handler in handlers:
        dispatcher.add_handler(handler)
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == '__main__':
    main()
