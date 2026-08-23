import os
import json
import random
import urllib.parse
import urllib.request
import urllib.error


# ============================================================
# PANGVA AI BOT
# AI-помощник сообщества Pangva School
# ============================================================


# Секретные ключи берутся из GitHub Secrets.
# СЮДА НИКАКИЕ КЛЮЧИ ВСТАВЛЯТЬ НЕ НУЖНО.

VK_TOKEN = os.environ.get("VK_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


# Версия VK API
VK_API_VERSION = "5.199"

# Бесплатные модели OpenRouter
OPENROUTER_MODEL = "openrouter/free"


# ============================================================
# ТЕКСТ СПРАВКИ
# ============================================================

HELP_TEXT = """
👋 Я Pangva AI — AI-помощник для преподавателей английского языка.

Я могу помочь:

💬 Speaking
Создать вопросы и темы для обсуждения.

🎲 Activities
Придумать warm-up, игру или активность для урока.

📚 Grammar
Объяснить грамматику и создать упражнения.

📝 Vocabulary
Создать задания на лексику.

🎯 Lesson ideas
Предложить идеи для урока под уровень A1–C1.

👩‍🏫 Lesson planning
Помочь составить небольшой план урока.

✍️ English
Проверить или улучшить английские предложения.

Например, напишите:

«Придумай warm-up на тему Food для A2»

«Создай 8 speaking questions на тему Travelling для B1»

«Объясни Present Perfect простыми словами»

«Составь мини-урок на тему Hobbies для подростка B1»

🤖 Ответы создаются с помощью искусственного интеллекта.
""".strip()


# ============================================================
# ИНСТРУКЦИЯ ДЛЯ ИИ
# ============================================================

SYSTEM_PROMPT = """
Ты — Pangva AI, виртуальный AI-помощник сообщества Pangva School.

Pangva School — сообщество с практическими и методическими
материалами для преподавателей английского языка.

Твоя основная аудитория — преподаватели английского языка.

Ты помогаешь:

- придумывать warm-up activities;
- создавать speaking questions;
- придумывать игры для уроков;
- создавать упражнения по лексике и грамматике;
- объяснять английскую грамматику;
- адаптировать задания под уровни A1-C1;
- создавать задания для детей, подростков и взрослых;
- придумывать темы для дискуссий;
- составлять небольшие планы уроков;
- проверять английские предложения;
- улучшать формулировки на английском языке;
- давать практические идеи для занятий;
- создавать материалы, которые преподаватель сможет
  использовать прямо на уроке.

ПРАВИЛА:

1. Если пользователь пишет по-русски — отвечай по-русски.

2. Если пользователь просит создать вопросы, упражнения,
текст, диалог или другой учебный материал на английском,
сам учебный материал пиши на английском.

3. Если указан уровень A1, A2, B1, B2, C1 —
обязательно учитывай этот уровень.

4. Если указан возраст или тип ученика
(ребёнок, подросток, взрослый) — учитывай это.

5. Ответ должен быть практическим.
Преподаватель должен иметь возможность использовать
результат на уроке.

6. Используй списки и понятную структуру,
когда это делает ответ удобнее.

7. Не делай ответы слишком длинными без необходимости.

8. Если запрос непонятен, задай один короткий
уточняющий вопрос.

9. Не придумывай конкретные товары, курсы или материалы
Pangva School, если пользователь сам их не назвал.

10. Не утверждай, что у Pangva School есть конкретный
материал или товар, если такой информации тебе не дали.

Будь доброжелательным, понятным и профессиональным.
""".strip()


# ============================================================
# ЗАПРОС К VK API
# ============================================================

def vk_api(method, params=None):

    if not VK_TOKEN:
        raise RuntimeError(
            "VK_TOKEN не найден в GitHub Secrets"
        )

    if params is None:
        params = {}

    params["access_token"] = VK_TOKEN
    params["v"] = VK_API_VERSION

    data = urllib.parse.urlencode(
        params
    ).encode("utf-8")

    url = (
        "https://api.vk.com/method/"
        + method
    )

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            response_text = (
                response
                .read()
                .decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        error_text = (
            error
            .read()
            .decode(
                "utf-8",
                errors="ignore"
            )
        )

        raise RuntimeError(
            f"VK HTTP error {error.code}: "
            f"{error_text}"
        )

    result = json.loads(
        response_text
    )

    if "error" in result:

        raise RuntimeError(
            "Ошибка VK API: "
            + json.dumps(
                result["error"],
                ensure_ascii=False
            )
        )

    return result.get(
        "response"
    )


# ============================================================
# ЗАПРОС К ИСКУССТВЕННОМУ ИНТЕЛЛЕКТУ
# ============================================================

def ask_ai(user_text):

    if not OPENROUTER_API_KEY:

        raise RuntimeError(
            "OPENROUTER_API_KEY не найден "
            "в GitHub Secrets"
        )

    payload = {

        "model":
            OPENROUTER_MODEL,

        "messages": [

            {
                "role":
                    "system",

                "content":
                    SYSTEM_PROMPT
            },

            {
                "role":
                    "user",

                "content":
                    user_text
            }
        ],

        "temperature":
            0.7,

        "max_tokens":
            700
    }

    body = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(

        "https://openrouter.ai/api/v1/chat/completions",

        data=body,

        method="POST",

        headers={

            "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

            "Content-Type":
                "application/json",

            "X-Title":
                "Pangva AI Bot"
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            response_text = (
                response
                .read()
                .decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        error_text = (
            error
            .read()
            .decode(
                "utf-8",
                errors="ignore"
            )
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

    except Exception as error:

        print(
            "Ошибка соединения с OpenRouter:",
            error
        )

        return (
            "Сейчас не удалось связаться с ИИ. "
            "Попробуйте написать ещё раз чуть позже."
        )

    result = json.loads(
        response_text
    )

    choices = result.get(
        "choices",
        []
    )

    if not choices:

        print(
            "OpenRouter не вернул choices:",
            response_text
        )

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

    return str(
        content
    ).strip()


# ============================================================
# ОТПРАВКА СООБЩЕНИЯ В VK
# ============================================================

def send_vk_message(
    peer_id,
    text
):

    text = str(
        text
    ).strip()

    if not text:
        return

    # Ограничиваем очень длинные ответы
    if len(text) > 4000:

        text = (
            text[:4000]
            + "\n\n[Ответ был сокращён]"
        )

    vk_api(
        "messages.send",
        {
            "peer_id":
                peer_id,

            "random_id":
                random.randint(
                    1,
                    2147483647
                ),

            "message":
                text
        }
    )


# ============================================================
# ПОЛУЧАЕМ НЕПРОЧИТАННЫЕ ДИАЛОГИ
# ============================================================

def get_unread_conversations():

    result = vk_api(
        "messages.getConversations",
        {
            "filter":
                "unread",

            "count":
                20
        }
    )

    if not result:
        return []

    return result.get(
        "items",
        []
    )


# ============================================================
# ПОМЕЧАЕМ ДИАЛОГ ПРОЧИТАННЫМ
# ============================================================

def mark_as_read(
    peer_id
):

    vk_api(
        "messages.markAsRead",
        {
            "peer_id":
                peer_id
        }
    )


# ============================================================
# ПРОВЕРЯЕМ, ПРОСИТ ЛИ ПОЛЬЗОВАТЕЛЬ СПРАВКУ
# ============================================================

def is_help_request(
    user_text
):

    normalized = (
        user_text
        .lower()
        .strip()
    )

    help_commands = {

        "помощь",
        "помоги",
        "что ты умеешь",
        "что ты умеешь?",
        "что умеешь",
        "что умеешь?",
        "help",
        "start",
        "старт",
        "начать",
        "меню"
    }

    return (
        normalized
        in help_commands
    )


# ============================================================
# ОБРАБОТКА ОДНОГО СООБЩЕНИЯ
# ============================================================

def process_message(
    message
):

    # Не отвечаем на исходящие сообщения сообщества
    if message.get("out") == 1:
        return

    peer_id = message.get(
        "peer_id"
    )

    if not peer_id:
        return

    user_text = str(
        message.get(
            "text",
            ""
        )
    ).strip()

    print(
        "Получено сообщение:",
        user_text
        if user_text
        else "[без текста]"
    )

    # ----------------------------------------
    # Если пользователь прислал не текст
    # ----------------------------------------

    if not user_text:

        answer = (
            "Пока я лучше всего понимаю "
            "текстовые сообщения. 😊\n\n"
            "Напишите ваш вопрос словами, например:\n"
            "«Придумай warm-up на тему Food для A2»."
        )

        send_vk_message(
            peer_id,
            answer
        )

        mark_as_read(
            peer_id
        )

        print(
            "Отправлен ответ на сообщение без текста"
        )

        return

    # ----------------------------------------
    # Команда помощи
    # ----------------------------------------

    if is_help_request(
        user_text
    ):

        send_vk_message(
            peer_id,
            HELP_TEXT
        )

        mark_as_read(
            peer_id
        )

        print(
            "Отправлена справка Pangva AI"
        )

        return

    # ----------------------------------------
    # Обычный запрос передаём ИИ
    # ----------------------------------------

    try:

        answer = ask_ai(
            user_text
        )

    except Exception as error:

        print(
            "Ошибка при обращении к ИИ:",
            error
        )

        answer = (
            "Сейчас произошла ошибка "
            "при обращении к ИИ. "
            "Попробуйте написать ещё раз позже."
        )

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


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():

    print(
        "Pangva AI Bot started"
    )

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

        if not message:
            continue

        try:

            process_message(
                message
            )

        except Exception as error:

            print(
                "Ошибка обработки сообщения:",
                error
            )


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    main()
