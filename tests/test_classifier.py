import pytest
from pathlib import Path
from src.email_reader import Email
from src.email_classifier import EmailClassifier

@pytest.fixture
def classifier():
    return EmailClassifier()

def make_email(subject="", sender="", body="", parse_error=False):
    e = Email(path=Path("test.txt"))
    e.subject = subject
    e.sender = sender
    e.body = body
    e.parse_error = parse_error
    return e

#Тесты инцидентов
@pytest.mark.parametrize("subject,expected", [
    ("URGENT: Массовый сбой авторизации", "incidents"),
    ("Критический инцидент — GitLab недоступен", "incidents"),
    ("Падает Service Desk, работа остановлена", "incidents"),
    ("Срочно: не работает Active Directory", "incidents"),
])
def test_classifies_incidents(classifier, subject, expected):
    result = classifier.classify(make_email(subject=subject))
    assert result.category == expected

#Тесты спама
@pytest.mark.parametrize("subject,expected", [
    ("Вы выиграли iPhone 15!", "spam"),
    ("Требуется срочная верификация аккаунта", "spam"),
    ("Exclusive offer — limited time", "spam"),
])
def test_classifies_spam(classifier, subject, expected):
    result = classifier.classify(make_email(subject=subject))
    assert result.category == expected

#Тесты мониторинга
@pytest.mark.parametrize("subject,sender,expected", [
    ("[CRITICAL] Disk usage > 75% на prod", "", "monitoring"),
    ("Плановый отчёт мониторинга", "alerts@grafana.internal", "monitoring"),
    ("[WARNING] Disk usage > 80%", "noreply@monitoring.internal", "monitoring"),
])
def test_classifies_monitoring(classifier, subject, sender, expected):
    result = classifier.classify(make_email(subject=subject, sender=sender))
    assert result.category == expected

#Тесты оборудования 
@pytest.mark.parametrize("subject,expected", [
    ("Неисправность оборудования: гарнитура", "hardware"),
    ("Проблема с принтер", "hardware"),
    ("Сломался гарнитура — нужна замена", "hardware"),
])
def test_classifies_hardware(classifier, subject, expected):
    result = classifier.classify(make_email(subject=subject))
    assert result.category == expected

#Тесты запросов доступа
@pytest.mark.parametrize("subject,expected", [
    ("Запрос доступа к VPN", "access_requests"),
    ("Нет доступа к GitLab после перевода", "access_requests"),
    ("Нужны права в 1C для нового сотрудника", "access_requests"),
])
def test_classifies_access_requests(classifier, subject, expected):
    result = classifier.classify(make_email(subject=subject))
    assert result.category == expected


#Тесты HR
@pytest.mark.parametrize("subject,expected", [
    ("Заявка на отпуск", "hr"),
    ("Больничный лист", "hr"),
    ("Изменение графика работы", "hr"),
])
def test_classifies_hr(classifier, subject, expected):
    result = classifier.classify(make_email(subject=subject))
    assert result.category == expected


#Тесты документов
@pytest.mark.parametrize("subject,expected", [
    ("Счёт на оплату №4008", "documents"),
    ("Закрывающие документы за декабрь", "documents"),
    ("Финальная версия: договор", "documents"),
])
def test_classifies_documents(classifier, subject, expected):
    result = classifier.classify(make_email(subject=subject))
    assert result.category == expected

#Мсключение
def test_empty_email_is_unknown(classifier):
    result = classifier.classify(make_email())
    assert result.category == "unknown"

def test_parse_error_is_unknown(classifier):
    result = classifier.classify(make_email(parse_error=True))
    assert result.category == "unknown"

def test_unknown_has_low_confidence(classifier):
    result = classifier.classify(make_email(subject="Абракадабра xyz 99999"))
    assert result.category == "unknown"
    assert result.confidence == "low"

def test_spam_beats_incidents(classifier):
    email = make_email(
        subject="URGENT: Требуется срочная верификация аккаунта",
    )
    result = classifier.classify(email)
    assert result.category == "spam"
    
@pytest.fixture
def high_confidence_cases():
    return [
        (make_email(subject="Вы выиграли iPhone 15!"), "spam"),
        (make_email(subject="Массовый сбой авторизации"), "incidents"),
        (make_email(subject="Неисправность оборудования: ноутбук"), "hardware"),
        (make_email(subject="Заявка на отпуск"), "hr"),
        (make_email(subject="Счёт на оплату №1234"), "documents"),
    ]

@pytest.mark.parametrize("index", [0, 1, 2, 3, 4])
def test_high_confidence_cases(classifier, high_confidence_cases, index):
    email, expected_category = high_confidence_cases[index]
    result = classifier.classify(email)
    assert result.category == expected_category
    assert result.confidence == "high"
