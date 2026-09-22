TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_regions",
            "description": (
                "Получить список крупных блоков страницы (шапка, основной контент, "
                "футер и т.п.) с количеством интерактивных элементов в каждом. "
                "Вызывай это первым на больших страницах, ПЕРЕД list_elements, "
                "чтобы понять, в каком блоке искать нужный элемент, вместо того "
                "чтобы сразу запрашивать все элементы страницы целиком."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_elements",
            "description": (
                "Получить список кликабельных элементов (ссылки, кнопки, поля ввода) "
                "с их id, тегом и текстом. Если страница большая, сначала вызови "
                "list_regions и передай region_id нужного блока, чтобы не получить "
                "слишком много элементов сразу. Если region_id не передан — "
                "возвращаются элементы со всей страницы."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "region_id": {
                        "type": "integer",
                        "description": "id региона из list_regions. Необязателен.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Сколько элементов вернуть. По умолчанию 40."
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Смещение для пагинации."
                    },
                    "query": {
                        "type": "string",
                        "description": "Фильтр по подстроке в тексте элемента. Необязателен."
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Кликнуть по элементу с указанным id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_id": {"type": "integer", "description": "id элемента из list_elements"},
                },
                "required": ["element_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Ввести текст в поле с указанным id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_id": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["element_id", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "goto",
            "description": "Перейти по указанному URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": (
                "Задать уточняющий вопрос пользователю и дождаться ответа. "
                "Используй, если без ответа не можешь продолжить: не знаешь URL, "
                "непонятно, какой из нескольких вариантов выбрать, нужны учётные "
                "данные и т.п."
            ),
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "current_url",
            "description": "Вызывай, когда надо проверить или убедиться, какой url сейчас открыт.",
            "parameters": {},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Вызови, когда задача выполнена. Передай краткий итог того, что сделано.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
        },
    },
]
