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
BITRIX_WEBHOOK_URL = 'https://veleres.bitrix24.ru/rest/30/i2imc8wqu35pmdem/'
NOTIFY_USER_ID = '30'  # ID пользователя для уведомлений


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

        if event == 'ONCRMLEADADD':
            # Обрабатываем создание лида
            lead_id = data['data[FIELDS][ID]']
            logger.info(f"Обрабатываем лид с ID: {lead_id}")

            # Проверяем повторные звонки
            #result = check_repeat_calls_for_deal(lead_id)

            # отправляем уведомление
            result = send_notification(lead_id)

            return jsonify({'status': 'success', 'send_message': result})

        else:
            logger.warning(f"Неизвестное событие: {event}")
            return jsonify({'status': 'ignored', 'event': event})

    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_deal_data(deal_id):
    """
    Получает данные сделки по ID
    """
    try:
        response = requests.post(
            f'{BITRIX_WEBHOOK_URL}crm.deal.get',
            json={'id': deal_id}
        )

        if response.status_code == 200:
            return response.json().get('result', {})
        else:
            logger.error(f"Ошибка получения сделки: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка запроса сделки: {str(e)}")
        return None

def send_notification(lead_id):
    """
    Отправляет уведомление в Bitrix24
    """
    try:
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

        message = f"Создан лид с ID: {lead_id}"

        requests.post(
            f'{BITRIX_WEBHOOK_URL}im.notify.system.add',
            json={
                'USER_ID': NOTIFY_USER_ID,
                'message': message
            }
        )

        logger.info(f"Уведомление отправлено для лида {lead_id}")
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