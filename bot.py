import os
import json
import random
import urllib.parse
import urllib.request
import urllib.error


# ==========================================
# НАСТРОЙКИ
# ==========================================

VK_TOKEN = os.environ.get("VK_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

VK_API_VERSION = "5.199"

OPENROUTER_MODEL = "openrouter/free"


# ==========================================
# ОБЩАЯ ФУНКЦИЯ ДЛЯ VK API
# ==========================================

def vk_api(method, params=None):

    if not VK_TOKEN:
        raise RuntimeError("VK_TOKEN не найден")

    if params is None:
        params = {}

    params["access_token"] = VK_TOKEN
    params["v"] = VK_API_VERSION

    data = urllib.parse.urlencode(params).encode("utf-8")

    url = f"https://api.vk.com/method/{method}"

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    if "error" in result:
        raise RuntimeError(
            f"Ошибка VK API: {result['error']}"
        )

    return result.get("response")


# ==========================================
# ЗАПРОС К ИИ
# ==========================================

def ask_ai(user_text):

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY не найден"
        )

    system_prompt = """
Ты — AI-помощник сообщества Pangva School.

Pangva School — сообщество с практическими
и методическими материалами для преподавателей
английского языка.

Ты помогаешь преподавателям английского языка.

Ты умеешь:
- придумывать задания для уроков;
- создавать speaking questions;
- придумывать warm-up activities;
- объяснять английскую грамматику;
- создавать упражнения;
- придумывать игры;
- адаптировать задания под уровни A1-C1;
- создавать задания для детей, подростков и взрослых;
- помогать с лексикой;
- проверять английские предложения;
- улучшать формулировки на английском;
- придумывать темы для дискуссий;
- составлять небольшие планы уроков.

Если пользователь пишет по-русски —
отвечай по-русски.

Если пользователь просит создать материал
на английском языке —
сам материал пиши на английском.

Отвечай понятно, доброжелательно и практически.

Не делай ответ слишком длинным,
если пользователь сам этого не просит.
"""

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

            "Content-Type":
                "application/json"
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        error_text = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        print(
            "Ошибка OpenRouter:",
            error.code,
            error_text
        )

        if error.code == 429:
            return (
                "Сейчас достигнут лимит бесплатных "
                "запросов к ИИ. Попробуйте немного позже."
            )

        return (
            "Сейчас ИИ временно не может ответить. "
            "Попробуйте написать ещё раз чуть позже."
        )

    choices = result.get("choices", [])

    if not choices:
        return (
            "ИИ не смог сформировать ответ. "
            "Попробуйте задать вопрос ещё раз."
        )

    message = choices[0].get(
        "message",
        {}
    )

    content = message.get(
        "content",
        ""
    )

    if not content:
        return (
            "ИИ не смог сформировать ответ. "
            "Попробуйте задать вопрос ещё раз."
        )

    return content.strip()


# ==========================================
# ОТПРАВКА СООБЩЕНИЯ В VK
# ==========================================

def send_vk_message(peer_id, text):

    # На всякий случай ограничиваем
    # слишком длинный ответ
    if len(text) > 4000:
        text = (
            text[:4000]
            + "\n\n[Ответ сокращён]"
        )

    vk_api(
        "messages.send",
        {
            "peer_id": peer_id,
            "random_id": random.randint(
                1,
                2147483647
            ),
            "message": text
        }
    )


# ==========================================
# ПОЛУЧЕНИЕ НЕПРОЧИТАННЫХ ДИАЛОГОВ
# ==========================================

def get_unread_conversations():

    result = vk_api(
        "messages.getConversations",
        {
            "filter": "unread",
            "count": 20
        }
    )

    if not result:
        return []

    return result.get(
        "items",
        []
    )


# ==========================================
# ПОМЕЧАЕМ ДИАЛОГ ПРОЧИТАННЫМ
# ==========================================

def mark_as_read(peer_id):

    vk_api(
        "messages.markAsRead",
        {
            "peer_id": peer_id
        }
    )


# ==========================================
# ОСНОВНАЯ РАБОТА БОТА
# ==========================================

def main():

    print("Pangva AI Bot started")

    conversations = (
        get_unread_conversations()
    )

    print(
        "Непрочитанных диалогов:",
        len(conversations)
    )

    for item in conversations:

        message = item.get(
            "last_message",
            {}
        )

        # Не отвечаем на исходящие сообщения
        if message.get("out") == 1:
            continue

        peer_id = message.get(
            "peer_id"
        )

        user_text = str(
            message.get(
                "text",
                ""
            )
        ).strip()

        if not peer_id:
            continue

        if not user_text:
            continue

        print(
            "Получено сообщение:",
            user_text
        )

        try:

            answer = ask_ai(
                user_text
            )

        except Exception as error:

            print(
                "Ошибка ИИ:",
                error
            )

            answer = (
                "Сейчас произошла ошибка при обращении "
                "к ИИ. Попробуйте написать ещё раз позже."
            )

        try:

            send_vk_message(
                peer_id,
                answer
            )

            mark_as_read(
                peer_id
            )

            print(
                "Ответ успешно отправлен"
            )

        except Exception as error:

            print(
                "Ошибка VK:",
                error
            )


if __name__ == "__main__":
    main()
