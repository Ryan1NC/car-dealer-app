from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
import sys

from generated_ui.main_window import Ui_MainWindow
from generated_ui.history import Ui_History
from generated_ui.order import Ui_Order


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.history_window = HistoryWindow()
        self.order_window = OrderWindow()
        #привязки кнопок к открытиям окон
        self.ui.all_orders.clicked.connect(self.open_history)
        self.ui.make_an_order.clicked.connect(self.open_order)

    def open_history(self):
        self.history_window.show()

    def open_order(self):
        self.order_window.show()

class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_History()
        self.ui.setupUi(self)
        self.model = QSqlTableModel()
        self.model.setTable("История заказов")
        self.ui.tableView.setModel(self.model)

        # подгон таблицы к размеру
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.resizeRowsToContents()

        # первая загрузка данных
        self.load_data()

    def load_data(self):  #функция для обновления данных
        self.model.select()

    def showEvent(self, event):
        # при открытии окна обновляем данные
        self.load_data()
        super().showEvent(event)


class OrderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Order()
        self.ui.setupUi(self)
        #цены раскрасок
        self.colors = {
            "Белый (+200)": 200,
            "Чёрный (+500)": 500,
            "Серый (+700)": 700,
            "Красный (+600)": 600,
            "Синий (+500)": 500,
        }
        self.ui.car_choose_2.addItems(self.colors.keys())
        self.load_cars()
        if self.ui.car_choose.count() > 0:
            self.ui.car_choose.setCurrentIndex(0) #заранее выбираем 1ю возможную машину
            self.update_price()  # вызов функции пересчёта цены

        self.base_price = 0
        #при изменении выбора опций меняем цену
        self.ui.car_choose.currentIndexChanged.connect(self.update_price)
        self.ui.car_choose_2.currentIndexChanged.connect(self.update_price)
        self.ui.option0.stateChanged.connect(self.update_price)
        self.ui.option1.stateChanged.connect(self.update_price)
        self.ui.option2.stateChanged.connect(self.update_price)
        self.ui.option3.stateChanged.connect(self.update_price)
        #вызов функции отправки заказа в бд
        self.ui.make_an_order.clicked.connect(self.create_order)

    def load_cars(self):
        #выбираем все существующие в бд машины
        self.ui.car_choose.clear()
        query = QSqlQuery("SELECT [Марка а/м], [Модель а/м], [Цена а/м] FROM Автомобили WHERE [В наличии] = 'Да'")
        while query.next():
            brand = query.value(0)
            model = query.value(1)
            price = query.value(2)
            self.ui.car_choose.addItem(f"{brand} {model}", price)

    def update_price(self):
        #функция подсчёёта и обновления цены
        self.base_price = self.ui.car_choose.currentData() or 0
        color_price = float(self.colors.get(self.ui.car_choose_2.currentText(), 0))
        options_price = sum([200.0 if self.ui.option0.isChecked() else 0,
                             150.0 if self.ui.option1.isChecked() else 0,
                             300.0 if self.ui.option2.isChecked() else 0,
                             500.0 if self.ui.option3.isChecked() else 0])
        total_price = self.base_price + color_price + options_price
        self.ui.label_6.setText(f"{total_price} у.е.")

    def create_order(self):
        #заносим данные в переменные для отправки в бд
        car_text = self.ui.car_choose.currentText()
        color_text = self.ui.car_choose_2.currentText().split(" ")[0]
        total_price = self.base_price + self.colors.get(self.ui.car_choose_2.currentText(), 0)

        # получаем ID автомобиля по названию марки и модели
        car_query = QSqlQuery()
        car_query.prepare("SELECT [ID а/м] FROM [Автомобили] WHERE [Марка а/м] + ' ' + [Модель а/м] = ?")
        car_query.addBindValue(car_text)
        if not car_query.exec_() or not car_query.next():
            print("Ошибка: не найден ID автомобиля для", car_text)
            return
        car_id = car_query.value(0)

        # получаем незанятый ID доп. опций
        options_query = QSqlQuery()
        options_query.exec_("SELECT MAX([ID заказа доп опций]) FROM [Доп. опции]")
        options_id = options_query.value(0) + 1 if options_query.next() and options_query.value(0) else 1

        # вставляем данные в таблицу Доп. опции
        options_query.prepare("""
            INSERT INTO [Доп. опции] ([ID заказа доп опций], [Комплект зимних шин], Бронеплёнка, [Литые диски], Парктроники)
            VALUES (?, ?, ?, ?, ?)
        """)
        options_query.addBindValue(options_id)
        options_query.addBindValue(int(self.ui.option0.isChecked()))
        options_query.addBindValue(int(self.ui.option1.isChecked()))
        options_query.addBindValue(int(self.ui.option2.isChecked()))
        options_query.addBindValue(int(self.ui.option3.isChecked()))

        if not options_query.exec_():
            print("Ошибка доп. опций:", options_query.lastError().text())
            return

        # получаем незанятый ID заказа
        history_query = QSqlQuery()
        history_query.exec_("SELECT MAX([Номер записи]) FROM [История заказов]")
        order_id = history_query.value(0) + 1 if history_query.next() and history_query.value(0) else 1

        # вставляем данные в таблицу История заказов
        history_query.prepare("""
            INSERT INTO [История заказов] ([Номер записи], [Дата сделки], [ID а/м], Цвет, [Продано за], [ID заказа доп опций])
            VALUES (?, GETDATE(), ?, ?, ?, ?)
        """)
        history_query.addBindValue(order_id)
        history_query.addBindValue(car_id)
        history_query.addBindValue(color_text)
        history_query.addBindValue(total_price)
        history_query.addBindValue(options_id)

        if not history_query.exec_():
            print("Ошибка добавления заказа:", history_query.lastError().text())
            return

        print(f"Заказ {order_id} оформлен")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    #подключение к бд
    db = QSqlDatabase.addDatabase("QODBC")
    db.setDatabaseName("DRIVER={SQL Server};SERVER=RNCMAGICBOOK14\\SQLEXPRESS;DATABASE=Autodealer;Trusted_Connection=yes")
    if not db.open():
        print("Ошибка подключения к базе данных")
        sys.exit(1)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
