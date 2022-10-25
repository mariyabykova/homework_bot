class ApiStatusCodeException(Exception):
    """Ошибка запроса к основному API:
    статус-код не равен 200."""
    pass


class HomeWorkIsNoneException(Exception):
    """Отсутствует значение homework_name."""
    pass


class HomeworkStatusIsNoneException(Exception):
    """У домашней работы отсутствует статус."""
    pass


class UndocumentedHomeworkStatusException(Exception):
    """Недокументированный статус домашней работы."""
    pass