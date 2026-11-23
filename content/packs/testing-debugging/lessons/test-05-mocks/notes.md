# Моки: подменяем зависимости

Тест должен быть быстрым и повторяемым. Время, случайность, сеть и файлы на время теста заменяют **двойниками** из `unittest.mock`.

```py
from unittest.mock import Mock, patch

fetch = Mock(return_value={"temp": 12})     # двойник: возвращает заданное
fetch("Краков")
print(fetch.call_count)                      # 1
fetch.assert_called_once_with("Краков")     # проверка вызова

broken = Mock(side_effect=ConnectionError("нет сети"))   # имитация сбоя

import time
with patch("time.time", return_value=1000.0):             # подмена внутри блока
    print(time.time())                                    # 1000.0
```

| Что | Как |
|---|---|
| вернуть значение | `Mock(return_value=…)` |
| выбросить ошибку | `Mock(side_effect=ConnectionError(...))` |
| вернуть по очереди | `Mock(side_effect=[1, 2, 3])` |
| сколько раз вызвали | `m.call_count`, `m.called` |
| с какими аргументами | `m.call_args`, `m.assert_called_once_with(...)` |
| подмена на время теста | `with patch("модуль.имя", return_value=…):` |

- `patch` подменяет имя там, куда вы показали: после `from time import time` у вашего кода своя ссылка, и подмена `time.time` её не задевает. Импортируйте модуль целиком (`import time`) и вызывайте `time.time()`.
- Подменяйте только границы (сеть, время, случайность, диск), но не проверяемый код.
- Проверяйте результат, а не каждый внутренний вызов: иначе тест ломается при любом рефакторинге.
- `Mock` принимает любые обращения, в том числе с опечаткой: проверяйте вызовы явно.
