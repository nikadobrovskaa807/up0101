import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
   QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem,
   QDialog, QFormLayout, QSpinBox, QComboBox, QDateEdit, QMessageBox
)

from fpdf import FPDF
import os
from PySide6.QtCore import Qt, QSize
from sqlalchemy import func
from modelsup import Partners, TypeCompany, Product, MaterialProduct, Material, PartnerProduct, ProductType, Connect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Функция для расчета необходимого материала
def calculate_material_needed(product_id, quantity):
    session = Connect.create_session()
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        raise ValueError("Продукт не найден.")
 
    materials = session.query(MaterialProduct).filter_by(id_product=product_id).all()
    total_material_needed = 0
 
    for material_product in materials:
        material = session.query(Material).filter_by(id=material_product.id_material).first()
        if not material:
            continue
        # Расчет материала с учетом брака
        material_needed = product.size * quantity * material.defect
        total_material_needed += material_needed
 
    return total_material_needed

def calculate_discount(partner_id: int) -> float:
   """Функция для расчета скидки на основе объема продаж партнера"""
   # Получаем все продажи партнера по его id
   session = Connect.create_session()
   sales = session.query(PartnerProduct).filter(PartnerProduct.id_partner == partner_id).all()

   # Суммируем общее количество продукции
   total_sales = sum(sale.quantity for sale in sales)

   # Рассчитываем скидку в зависимости от объема продаж
   if total_sales <= 10000:
       discount = 0  # 0% скидка
   elif total_sales <= 50000:
       discount = 5  # 5% скидка
   elif total_sales <= 300000:
       discount = 10  # 10% скидка
   else:
       discount = 15  # 15% скидка

   return discount

def calculate_discounts_for_all_partners():
   """Функция для расчета скидок для всех партнеров"""
   # Получаем всех партнеров
   session = Connect.create_session()
   partners = session.query(Partners).all()

   # Для каждого партнера рассчитываем скидку
   partner_discounts = {}
   for partner in partners:
       discount = calculate_discount(partner.id)
       partner_discounts[partner.company_name] = discount  # Записываем скидку для партнера

   return partner_discounts

class MasterApp(QWidget):
  def __init__(self):
      super().__init__()
      self.session = Connect.create_session()
      # Установка иконки приложения
      self.setWindowTitle("Мастер пол")
      self.setWindowIcon(QIcon("F:/aawe.png"))  # Иконка приложения
      self.setFixedSize(1440, 1024)

      # Главный макет
      main_layout = QVBoxLayout()
      main_layout.setContentsMargins(0, 0, 0, 0)
      main_layout.setSpacing(0)

      # Верхняя панель
      top_panel = QWidget()
      top_panel.setStyleSheet("background-color: #F4E8D3; padding: 5px;")
      top_layout = QHBoxLayout(top_panel)

      # Иконка и текст для верхней панели
      top_icon_label = QLabel()
      top_icon_label.setPixmap(QIcon("F:/aawe.png").pixmap(50, 50))
      top_label = QLabel("Мастер пол")
      top_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-left: 0px;")

      add_partner_button = QPushButton("Добавить партнёра")
      add_partner_button.setFixedWidth(150)
      add_partner_button.clicked.connect(self.add_partner)

      # Добавляем элементы в верхнюю панель
      top_layout.addWidget(top_icon_label)  # Иконка рядом с текстом
      top_layout.addWidget(top_label)
      top_layout.addWidget(add_partner_button)
      top_layout.addStretch()
      main_layout.addWidget(top_panel)
     
      # Добавляем кнопку "Отчёт по история"
      history_button = QPushButton("Отчёт по истории")
      history_button.setFixedWidth(150)
      history_button.clicked.connect(self.export_to_pdf)
      top_layout.addWidget(history_button)

      # Панель навигации и содержимого
      content_layout = QHBoxLayout()
      left_panel = QWidget()
      left_panel.setFixedWidth(200)
      left_panel.setStyleSheet("background-color: #F4E8D3;")

      left_layout = QVBoxLayout(left_panel)
      left_layout.setAlignment(Qt.AlignTop)

      # Кнопки навигации с иконками
      self.partners_button = QPushButton("Партнёры")
      self.partners_button.setIcon(QIcon("F:/aawe.png")) # Иконка партнёров
      self.partners_button.setCheckable(True)
      self.partners_button.setChecked(True)
      self.partners_button.clicked.connect(self.select_partners_tab)

      self.history_button = QPushButton("История")
      self.history_button.setIcon(QIcon("F:/aawe.png")) # Иконка истории
      self.history_button.setCheckable(True)
      self.history_button.clicked.connect(self.select_history_tab)

      self.update_tab_styles()

      left_layout.addWidget(self.partners_button)
      left_layout.addWidget(self.history_button)

      right_panel = QWidget()
      self.right_layout = QVBoxLayout(right_panel)
      self.right_layout.setContentsMargins(10, 10, 10, 0)

      self.partners_list = QListWidget()
      self.partners_list.setSpacing(5)
      self.partners_list.setStyleSheet("border: 1px black;")
      self.partners_list.itemClicked.connect(self.highlight_selected_partner)
      self.partners_list.itemDoubleClicked.connect(self.edit_partner)

      self.load_partners_from_db()

      self.history_table = QTableWidget()
      self.history_table.setColumnCount(4)
      self.history_table.setHorizontalHeaderLabels(["Продукция", "Наименование партнёра", "Количество продукции", "Дата продажи"])

      self.right_layout.addWidget(self.partners_list)
      content_layout.addWidget(left_panel)
      content_layout.addWidget(right_panel)
      main_layout.addLayout(content_layout)
      self.setLayout(main_layout)

  def load_partners_from_db(self):
      self.partners_list.clear()
      session = Connect.create_session()
      partners = session.query(Partners).all()
      for partner in partners:
          item = QListWidgetItem()
          item_widget = self.create_partner_item(partner)
          item.setSizeHint(QSize(item_widget.sizeHint().width(), item_widget.sizeHint().height() + 20))
          self.partners_list.addItem(item)
          self.partners_list.setItemWidget(item, item_widget)
          item.setData(Qt.UserRole, partner)  # Сохраняем объект партнёра в item

  def create_partner_item(self, partner=None):
       item_widget = QWidget()
       layout = QVBoxLayout(item_widget)
       layout.setContentsMargins(10, 10, 10, 10)

       item_widget.setStyleSheet("""
            border: 1px solid #CCCCCC;  /* Светло-серая обводка */
            border-radius: 5px;        /* Закругленные углы */
            padding: 5px;             /* Отступ внутри */
        """)

       if partner:
           type_name = partner.type_company.name if partner.type_company else "Неизвестный тип"
           type_label = QLabel(f"{type_name} | {partner.company_name}")
           director_label = QLabel(f"Директор: {partner.director_name}")
           phone_label = QLabel(f"Телефон: {partner.phone}")
           rating_label = QLabel(f"Рейтинг: {partner.rating}")

           # Рассчитываем скидку
           discount = calculate_discount(partner.id)
           discount_label = QLabel(f"{discount}%")  # Создаем лейбл для скидки

           # Создаем горизонтальное размещение для названия компании и скидки
           company_layout = QHBoxLayout()
           company_layout.addWidget(type_label)
           company_layout.addStretch()  # Добавляем растягивающий элемент, чтобы скидка оказалась справа
           company_layout.addWidget(discount_label)

           item_widget.setProperty("partner_id", partner.id)  # Добавляем ID партнёра как свойство
       else:
           type_label = QLabel("Тип | Наименование партнёра")
           director_label = QLabel("Директор")
           phone_label = QLabel("+7 223 322 22 32")
           rating_label = QLabel("Рейтинг: 10")
           discount_label = QLabel("0%")  # По умолчанию скидка 0%

       # Добавляем лейблы в вертикальный макет
       layout.addLayout(company_layout)  # Добавляем горизонтальное расположение для компании и скидки
       layout.addWidget(director_label)
       layout.addWidget(phone_label)
       layout.addWidget(rating_label)
       item_widget.setStyleSheet("padding: 5px;")
       
       return item_widget

  def update_tab_styles(self):
      self.partners_button.setStyleSheet("padding: 10px; background-color: #67BA80;" if self.partners_button.isChecked() else "color: black;")
      self.history_button.setStyleSheet("padding: 10px; background-color: #67BA80;" if self.history_button.isChecked() else "color: black;")

  def select_partners_tab(self):
      self.partners_button.setChecked(True)
      self.history_button.setChecked(False)
      self.update_tab_styles()
      self.right_layout.removeWidget(self.history_table)
      self.history_table.setParent(None)
      self.right_layout.addWidget(self.partners_list)

  def select_history_tab(self):
      self.history_button.setChecked(True)
      self.partners_button.setChecked(False)
      self.update_tab_styles()
      self.right_layout.removeWidget(self.partners_list)
      self.partners_list.setParent(None)
      self.right_layout.addWidget(self.history_table)

  def highlight_selected_partner(self, item):
      for i in range(self.partners_list.count()):
          widget = self.partners_list.itemWidget(self.partners_list.item(i))
          widget.setStyleSheet("background-color: #FFFFFF; padding: 5px;")
      selected_widget = self.partners_list.itemWidget(item)
      selected_widget.setStyleSheet("background-color: #67BA80; color: #FFFFFF; padding: 5px;")

  def edit_partner(self, item):
      partner = item.data(Qt.UserRole)
      self.show_partner_edit_dialog(partner)

  def show_partner_edit_dialog(self, partner):
       dialog = QDialog(self)
       dialog.setWindowTitle(f"Редактировать партнёра: {partner.company_name}")
       dialog.setStyleSheet("background-color: white")
       dialog.setFixedSize(600, 300)
       form_layout = QFormLayout(dialog)

       name_edit = QLineEdit(partner.company_name)
       ur_adress_edit = QLineEdit(partner.ur_adress)
       inn_edit = QLineEdit(partner.inn)
       director_name_edit = QLineEdit(partner.director_name)
       phone_edit = QLineEdit(partner.phone)
       email_edit = QLineEdit(partner.email)
       rating_edit = QSpinBox()
       rating_edit.setValue(partner.rating if partner.rating else 0)

       # Добавляем выпадающий список для типа партнёра с данными из БД
       partner_type_combo = QComboBox()
       session = Connect.create_session()
       types = session.query(TypeCompany).all()
       for type_ in types:
           partner_type_combo.addItem(type_.name, type_.id)

       form_layout.addRow("Наименование партнёра:", name_edit)
       form_layout.addRow("Тип партнёра:", partner_type_combo)
       form_layout.addRow("Юридический адрес:", ur_adress_edit)
       form_layout.addRow("ИНН:", inn_edit)
       form_layout.addRow("Имя директора:", director_name_edit)
       form_layout.addRow("Телефон:", phone_edit)
       form_layout.addRow("Email:", email_edit)
       form_layout.addRow("Рейтинг:", rating_edit)

       save_button = QPushButton("Сохранить")
       save_button.setStyleSheet("background-color: #67BA80; color: white; padding: 5px; margin-top: 20px;")
       save_button.clicked.connect(lambda: self.save_partner_changes(dialog, type_.id, partner_type_combo, name_edit, ur_adress_edit, inn_edit, director_name_edit, phone_edit, email_edit, rating_edit))
       form_layout.addWidget(save_button)

       # Кнопка удаления
       delete_button = QPushButton("Удалить")
       delete_button.setStyleSheet("background-color: black; color: white; padding: 5px; margin-top: 20px;")
       delete_button.clicked.connect(lambda: self.delete_partner(dialog, type_.id, partner_type_combo, name_edit, ur_adress_edit, inn_edit, director_name_edit, phone_edit, email_edit, rating_edit))
       form_layout.addWidget(delete_button)
       
       # Создаем горизонтальный макет для кнопок
       buttons_layout = QHBoxLayout()
       buttons_layout.addWidget(delete_button)  # Кнопка "Удалить" слева
       buttons_layout.addWidget(save_button)   # Кнопка "Сохранить" справа
       
       form_layout.addRow(buttons_layout)
       
       dialog.exec()

  def delete_partner(self, dialog, id, partner_type_combo, name_edit, ur_adress_edit, inn_edit, director_name_edit, phone_edit, email_edit, rating_edit):
       # Запрос на подтверждение удаления
       confirmation = QMessageBox.question(dialog, "Подтверждение",
                                       f"Вы уверены, что хотите удалить партнёра {id.company_name}?",
                                       QMessageBox.Yes | QMessageBox.No)
      
       if confirmation == QMessageBox.Yes:
           try:
               session = Connect.create_session()
               session.delete(id)  # Удаляем партнёра из базы данных
               session.commit()  # Подтверждаем изменения
               QMessageBox.information(dialog, "Удаление", "Партнёр был успешно удалён")
               dialog.accept()  # Закрываем диалог
               self.load_partners_from_db()  # Обновляем список партнёров
           except Exception as e:
               session.rollback()  # Откатываем изменения в случае ошибки
               QMessageBox.warning(dialog, "Ошибка", f"Ошибка при удалении партнёра: {e}")

  def save_partner_changes(self, dialog, id, partner_type_combo, name_edit, ur_adress_edit, inn_edit, director_name_edit, phone_edit, email_edit, rating_edit):
    session = Connect.create_session()
    try:
        # Загружаем партнёра заново через сессию
        partner = session.query(Partners).get(id)
        if partner:
            # Обновляем данные партнёра
            partner.company_name = name_edit.text()
            partner.ur_adress = ur_adress_edit.text()
            partner.inn = inn_edit.text()
            partner.director_name = director_name_edit.text()
            partner.phone = phone_edit.text()
            partner.email = email_edit.text()
            partner.rating = rating_edit.value()
            partner.type_partner = partner_type_combo.currentData()  # Сохраняем ID типа партнёра
            
            session.commit()  # Сохраняем изменения в базе данных
            QMessageBox.information(dialog, "Изменения", "Изменения успешно сохранены")
            dialog.accept()  # Закрываем диалог и обновляем отображение
            self.load_partners_from_db()
            session = Connect.create_session()
            session.commit()
        else:
            QMessageBox.warning(dialog, "Ошибка", "Партнёр не найден")
    except Exception as e:
        session.rollback()  # Откатываем изменения в случае ошибки
        QMessageBox.warning(dialog, "Ошибка", f"Ошибка при сохранении изменений: {e}")
    finally:
        session.close()
     
  def add_partner(self):
       dialog = QDialog(self)
       dialog.setWindowTitle("Добавить нового партнёра")
       dialog.setStyleSheet("background-color: white;")  # Белый фон для диалога
       dialog.setFixedSize(600, 300)  # Увеличим размер окна диалога
       form_layout = QFormLayout(dialog)

       # Поля для ввода данных партнёра
       name_edit = QLineEdit()
       ur_adress_edit = QLineEdit()
       inn_edit = QLineEdit()
       director_name_edit = QLineEdit()
       phone_edit = QLineEdit()
       email_edit = QLineEdit()
       rating_edit = QSpinBox()
       rating_edit.setRange(0, 100)

       # Выпадающий список для выбора типа партнёра
       partner_type_combo = QComboBox()
       session = Connect.create_session()
       types = session.query(TypeCompany).all()
       for type_ in types:
           partner_type_combo.addItem(type_.name, type_.id)

       form_layout.addRow("Наименование партнёра:", name_edit)
       form_layout.addRow("Тип партнёра:", partner_type_combo)
       form_layout.addRow("Юридический адрес:", ur_adress_edit)
       form_layout.addRow("ИНН:", inn_edit)
       form_layout.addRow("Имя директора:", director_name_edit)
       form_layout.addRow("Телефон:", phone_edit)
       form_layout.addRow("Email:", email_edit)
       form_layout.addRow("Рейтинг:", rating_edit)

       save_button = QPushButton("Сохранить")
       save_button.setStyleSheet("background-color: #67BA80; color: white; padding: 5px; margin-top: 20px;")
       save_button.clicked.connect(lambda: self.save_new_partner(dialog, partner_type_combo, name_edit, ur_adress_edit, inn_edit, director_name_edit, phone_edit, email_edit, rating_edit))
       form_layout.addWidget(save_button)
       
       calculate_discounts_for_all_partners()

       dialog.exec()

  def save_new_partner(self, dialog, partner_type_combo, name_edit, ur_adress_edit, inn_edit, director_name_edit, phone_edit, email_edit, rating_edit):
       # Проверка на пустые значения
       if not name_edit.text() or not ur_adress_edit.text() or not inn_edit.text() or not director_name_edit.text() or not phone_edit.text() or not email_edit.text():
           # Сообщение об ошибке, если поля обязательные пустые
           QMessageBox.warning(dialog, "Ошибка", "Все поля обязательны для заполнения")
           return

       # Проверка правильности ИНН (например, 10 цифр для России)
       if len(inn_edit.text()) != 10 or not inn_edit.text().isdigit():
           QMessageBox.warning(dialog, "Ошибка", "ИНН должен состоять из 10 цифр")
           return

       # Проверка на правильность типа партнёра
       type_partner_id = partner_type_combo.currentData()
       if not type_partner_id:
           QMessageBox.warning(dialog, "Ошибка", "Выберите тип партнёра")
           return

       # Создаем новый объект партнёра
       new_partner = Partners(
           company_name=name_edit.text(),
           ur_adress=ur_adress_edit.text(),
           inn=inn_edit.text(),
           director_name=director_name_edit.text(),
           phone=phone_edit.text(),
           email=email_edit.text(),
           rating=rating_edit.value() if rating_edit.value() else None,  # Если рейтинг пустой, используем None
           type_partner=type_partner_id  # Сохраняем ID типа партнёра
       )

       try:
           session = Connect.create_session()
           session.add(new_partner)
           session.commit()
           dialog.accept()
           self.load_partners_from_db()
       except Exception as e:
           session.rollback()  # Откатываем изменения в случае ошибки
           QMessageBox.warning(dialog, "Ошибка", f"Произошла ошибка при сохранении: {str(e)}")

  def load_history_from_db(self):
        # Очистим таблицу истории перед загрузкой новых данных
        self.history_table.setRowCount(0)
        session = Connect.create_session()

        # Запрашиваем данные из таблицы PartnerProduct с присоединением к таблицам Product, ProductType и Partners
        history_records = (
            session.query(PartnerProduct, ProductType.name, Partners.company_name)
            .join(Product, PartnerProduct.id_product == Product.id)
            .join(ProductType, Product.type == ProductType.id)
            .join(Partners, PartnerProduct.id_partner == Partners.id)
            .all()
        )

        # Заполняем таблицу данными
        for row_idx, (partner_product, product_type_name, partner_name) in enumerate(history_records):
            self.history_table.insertRow(row_idx)

            # Столбец "Тип продукции"
            self.history_table.setItem(row_idx, 0, QTableWidgetItem(product_type_name))

            # Столбец "Наименование партнёра"
            self.history_table.setItem(row_idx, 1, QTableWidgetItem(partner_name))

            # Столбец "Количество продукции"
            self.history_table.setItem(row_idx, 2, QTableWidgetItem(str(partner_product.quantity)))

            # Столбец "Дата продажи"
            self.history_table.setItem(row_idx, 3, QTableWidgetItem(partner_product.date_of_sale.strftime("%Y-%m-%d")))

  def select_history_tab(self):
        self.history_button.setChecked(True)
        self.partners_button.setChecked(False)
        self.update_tab_styles()
        self.right_layout.removeWidget(self.partners_list)
        self.partners_list.setParent(None)
        self.right_layout.addWidget(self.history_table)
        self.load_history_from_db()  # Загрузка истории при переключении на вкладку

  def export_to_pdf(self):
        pdf_path = "report_history.pdf"
        pdf_canvas = canvas.Canvas(pdf_path, pagesize=A4)
        pdfmetrics.registerFont(TTFont('ArialRegular', 'ArialRegular.ttf'))
        pdf_canvas.setFont("ArialRegular", 12)

        # Устанавливаем начальные параметры для текста
        text_x = 50
        text_y = 800
        line_height = 20

        # Заголовок отчета
        pdf_canvas.setFont("ArialRegular", 14)
        pdf_canvas.drawString(text_x, text_y, "Отчет по истории реализации продукции")
        text_y -= line_height * 2  # Отступ после заголовка

        # Заголовки столбцов
        pdf_canvas.setFont("ArialRegular", 12)
        columns = ["Продукция", "Наименование партнёра", "Количество продукции", "Дата продажи"]
        for i, column in enumerate(columns):
            pdf_canvas.drawString(text_x + i * 120, text_y, column)
        text_y -= line_height

        # Заполнение строк таблицы из QTableWidget
        pdf_canvas.setFont("ArialRegular", 10)
        row_count = self.history_table.rowCount()
        for row in range(row_count):
            if text_y < 50:  # Если места на странице недостаточно, переходим на новую
                pdf_canvas.showPage()
                text_y = 800

            product_name = self.history_table.item(row, 0).text()
            partner_name = self.history_table.item(row, 1).text()
            quantity = self.history_table.item(row, 2).text()
            sale_date = self.history_table.item(row, 3).text()

            pdf_canvas.drawString(text_x, text_y, product_name)
            pdf_canvas.drawString(text_x + 120, text_y, partner_name)
            pdf_canvas.drawString(text_x + 240, text_y, quantity)
            pdf_canvas.drawString(text_x + 360, text_y, sale_date)
            text_y -= line_height

        pdf_canvas.save()
        QMessageBox.information(self, "Отчет", f"PDF отчет сохранен как {pdf_path}")

if __name__ == "__main__":
  app = QApplication(sys.argv)
  master_app = MasterApp()
  master_app.show()
  sys.exit(app.exec())