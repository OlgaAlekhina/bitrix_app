import sys

from flask import Flask, request, jsonify
import requests
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Только в консоль
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация
BITRIX_WEBHOOK_URL = ''
NOTIFY_USER_ID = ''  # ID пользователя для уведомлений


@app.route("/")
def hello():
    return "Timeweb Cloud + Flask = ❤️"


@app.route('/bitrix-webhook', methods=['POST'])
def handle_bitrix_webhook():
    """ Обработчик вебхука от Bitrix24 """
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Raw body: {request.data.decode('utf-8')}")

    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        logger.info(f"Получен вебхук: {data}")

        # Проверяем тип события
        event = data.get('event', '')

        if event in ('ONCRMLEADADD', 'ONCRMLEADUPDATE'):
            # Обрабатываем создание или обновление лида
            lead_id = data['data[FIELDS][ID]']
            logger.info(f"Обрабатываем лид с ID: {lead_id}")

            # Получаем данные лида
            lead_data = get_lead_data(lead_id)

            created = True if event == 'ONCRMLEADADD' else False

            # Отправляем системное уведомление мне в Битрикс
            result = send_notification(created, lead_data)

            return jsonify({'status': 'success', 'send_message': result})

        else:
            logger.warning(f"Неизвестное событие: {event}")
            return jsonify({'status': 'ignored', 'event': event})

    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_lead_data(lead_id):
    """
    Получает данные лида по ID
    """
    try:
        response = requests.post(
            f'{BITRIX_WEBHOOK_URL}crm.lead.get',
            json={'id': lead_id}
        )

        if response.status_code == 200:
            return response.json().get('result', {})
        else:
            logger.error(f"Ошибка получения сделки: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка запроса сделки: {str(e)}")
        return None

def send_notification(created, lead_data):
    """
    Отправляет уведомление в Bitrix24
    """
    try:
        action = 'Создан' if created else 'Изменен'
        id = lead_data.get('ID')
        title = lead_data.get('TITLE')
        name = lead_data.get('NAME')
        second_name = lead_data.get('SECOND_NAME')
        last_name = lead_data.get('LAST_NAME')
        company = lead_data.get('COMPANY_TITLE')
        returned = lead_data.get('IS_RETURN_CUSTOMER')
        source = lead_data.get('SOURCE_DESCRIPTION')
        comments = lead_data.get('COMMENTS')
        status = lead_data.get('STATUS_ID')
        status_description = lead_data.get('STATUS_DESCRIPTION')
        # message = f"""
        # 🔔 ПОВТОРНЫЙ ЗВОНОК НА ДРУГОЙ НОМЕР
        #
        # 📞 Телефон клиента: {phone}
        # 🔢 Предыдущий номер: {prev_number}
        # 🔢 Текущий номер: {current_number}
        # ⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        #
        # 📋 Ссылка на сделку: https://your-company.bitrix24.ru/crm/deal/details/{deal_id}/
        #
        # 🚨 Клиент звонил на разные номера! Проверьте возможные дубликаты.
        # """

        message = f""" 
        {action} лид: 
        ID - {id}
        Название - {title if title else 'нет информации'}
        Имя - {name if name else 'нет информации'}
        Отчество - {second_name if second_name else 'нет информации'}
        Фамилия - {last_name if last_name else 'нет информации'}
        Компания - {company if company else 'нет информации'}
        Повторный - {'нет' if returned == 'N' else 'да'}
        Статус - {status if status else 'нет информации'}
        Описание статуса - {status_description if status_description else 'нет информации'}
        Источник - {source if source else 'нет информации'}
        Комментарии - {comments if comments else 'нет информации'}
        """

        response = requests.post(
            f'{BITRIX_WEBHOOK_URL}im.notify.system.add',
            json={
                'USER_ID': NOTIFY_USER_ID,
                'message': message
            }
        )

        logger.info(f"Ответ Bitrix24: {response.status_code} - {response.text}")
        logger.info(f"Уведомление отправлено для лида {id}")
        return 'success'

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {str(e)}")
        return f'error: {str(e)}'

@app.route('/hello-flask', methods=['GET'])
def hello_flask():
    return 'Hello Flask!'


if __name__ == "__main__":
    port = 8000
    app.run(debug=True,host='0.0.0.0',port=port)