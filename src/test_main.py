import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication
from main import OrderWindow, MainWindow, HistoryWindow

#fixture для работы с pyqt
@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

#тесты main window
@pytest.fixture
def main_window(app):
    return MainWindow()
#функция вызова окна истории
def test_open_history_shows_window(main_window):
    main_window.open_history()
    assert main_window.history_window.isVisible()
#функция вызова окна заказа
def test_open_order_shows_window(main_window):
    main_window.open_order()
    assert main_window.order_window.isVisible()


#тесты history_window
@pytest.fixture
def history_window(app):
    return HistoryWindow()
#проверка, не крашит ли при загрузке данных
def test_load_data_does_not_crash(history_window):
    history_window.load_data()
#проверка, отображает ли окно
def test_show_event_triggers_load_data(history_window):
    history_window.show()
    assert history_window.isVisible()

# окно заказа
@pytest.fixture
def order_window(app):
    return OrderWindow()
#проверка, корректно ли работает логика выбора машины и рассчёта стоимости
def test_update_price_sets_correct_label(order_window):
    order_window.ui.car_choose.setCurrentIndex(0)
    order_window.ui.car_choose_2.setCurrentIndex(0)
    order_window.ui.option0.setChecked(True)
    order_window.update_price()
    text = order_window.ui.label_6.text()
    assert "у.е." in text
    assert float(text.replace(" у.е.", "").replace(",", ".")) > 0
#проверка, вменяемое ли количество машин загрузилось с бд (число в диапазоне от нуля до бесконечности)
def test_load_cars_does_not_crash(order_window):
    order_window.load_cars()
    assert order_window.ui.car_choose.count() >= 0
#проверка функции create_order без входных данных
def test_create_order_fails_wo_entries(order_window):
    try:
        order_window.create_order()
    except Exception as e:
        pytest.fail(f"create_order вызвал исключение: {e}")