TOOLS = [
    {
        "name": "goto",
        "description": "Перейти по указанному URL в текущей вкладке.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "go_back",
        "description": "Вернуться на предыдущую страницу в истории браузера.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_regions",
        "description": (
            "Получить список крупных блоков страницы (шапка, основной контент, "
            "футер и т.п.) с количеством интерактивных элементов в каждом. "
            "Вызывай это первым на больших страницах, ПЕРЕД list_elements, "
            "чтобы понять, в каком блоке искать нужный элемент."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_elements",
        "description": (
            "Получить список кликабельных элементов (ссылки, кнопки, поля ввода, "
            "select) с их id, тегом и текстом. Если region_id не передан — "
            "возвращаются элементы со всей страницы. Если сайт использует "
            "бесконечную прокрутку и нужного элемента не видно — сначала "
            "вызови scroll_page, потом list_elements заново."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region_id": {"type": "integer", "description": "id региона из list_regions. Необязателен."},
                "limit": {"type": "integer", "description": "Сколько элементов вернуть. По умолчанию 40."},
                "offset": {"type": "integer", "description": "Смещение для пагинации."},
                "query": {"type": "string", "description": "Фильтр по подстроке в тексте элемента."},
            },
        },
    },
    {
        "name": "read_text",
        "description": (
            "Прочитать видимый текст страницы или региона целиком (без списка "
            "элементов). Используй вместо list_elements, когда задача — "
            "«прочитай», «найди информацию», «что написано» и не требует клика: "
            "это дешевле и даёт связный текст, а не список кнопок."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"region_id": {"type": "integer", "description": "id региона из list_regions. Необязателен — по умолчанию вся страница."}},
        },
    },
    {
        "name": "click",
        "description": "Кликнуть по элементу с указанным id.",
        "input_schema": {
            "type": "object",
            "properties": {"element_id": {"type": "integer", "description": "id элемента из list_elements"}},
            "required": ["element_id"],
        },
    },
    {
        "name": "type_text",
        "description": "Ввести текст в поле с указанным id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "element_id": {"type": "integer"},
                "text": {"type": "string"},
                "submit": {"type": "boolean", "description": "Нажать Enter после ввода (для поиска и т.п.). По умолчанию false."},
            },
            "required": ["element_id", "text"],
        },
    },
    {
        "name": "select_option",
        "description": "Выбрать значение в выпадающем списке <select> по видимой подписи или значению.",
        "input_schema": {
            "type": "object",
            "properties": {
                "element_id": {"type": "integer"},
                "value": {"type": "string", "description": "Видимый текст опции или её value."},
            },
            "required": ["element_id", "value"],
        },
    },
    {
        "name": "scroll_page",
        "description": "Прокрутить страницу вверх/вниз — полезно для бесконечной ленты или чтобы найти скрытый элемент.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["down", "up"]},
                "amount": {"type": "integer", "description": "Пикселей. По умолчанию 1200."},
            },
            "required": ["direction"],
        },
    },
    {
        "name": "wait",
        "description": "Подождать до 5 секунд — использовать редко, только если странице явно нужно время догрузиться после действия.",
        "input_schema": {
            "type": "object",
            "properties": {"seconds": {"type": "number"}},
            "required": ["seconds"],
        },
    },
    {
        "name": "current_url",
        "description": "Получить текущий URL активной вкладки.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "ask_user",
        "description": (
            "Задать уточняющий вопрос пользователю и дождаться ответа. Используй, "
            "если без ответа не можешь продолжить: не знаешь URL, непонятно, какой "
            "из вариантов выбрать, нужны учётные данные и т.п."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
    {
        "name": "ask_page",
        "description": (
            "Задать конкретный вопрос о текущем состоянии страницы "
            "специализированному саб-агенту (он видит скриншот и/или текст "
            "страницы целиком) и получить короткий ответ. Используй это, "
            "когда нужно понять СОСТОЯНИЕ, а не список кнопок: прошла ли "
            "отправка формы, показана ли ошибка валидации, что реально "
            "произошло после клика. Особенно важно вызывать это после клика "
            "по кнопкам вида «Найти», «Отправить», «Продолжить», «Купить» — "
            "URL мог не измениться именно потому, что форма не прошла "
            "валидацию, и это стоит проверить, а не сразу пробовать другой путь."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
    {
        "name": "finish",
        "description": "Вызови, когда задача выполнена или дальше двигаться некуда. Передай краткий итог того, что сделано/найдено.",
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    },
]