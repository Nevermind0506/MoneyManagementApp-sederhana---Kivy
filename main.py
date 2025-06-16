import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

class TransactionHistory(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.size_hint_y = None
        self.spacing = 8
        self.padding = [8, 8, 8, 8]
        self.bind(minimum_height=self.setter('height'))

    def add_transaction(self, transaction):
        # Format: date | type | amount | description
        date_str = transaction.get('date', '')[:19].replace('T', ' ')
        ttype = transaction.get('type', '')
        amount = transaction.get('amount', 0)
        desc = transaction.get('description', '')
        color = get_color_from_hex("#10b981") if ttype == 'income' else get_color_from_hex("#ef4444")
        sign = '+' if ttype == 'income' else '-'
        label_text = f"{date_str} | {ttype.capitalize():8} | {sign}Rp {amount:,.0f} | {desc}"
        lbl = Label(text=label_text, size_hint_y=None, height=30, color=color, halign='left')
        lbl.bind(texture_size=lbl.setter('size'))
        lbl.text_size = (Window.width * 0.9, None)
        self.add_widget(lbl)

class FinanceTrackerApp(App):
    def build(self):
        self.title = "Pencatat Keuangan Harian untuk Pelajar"
        Window.size = (400, 700)

        self.transactions_file = "transactions.json"
        self.transactions = []
        self.balance = 0.0

        root_layout = BoxLayout(orientation='vertical', padding=16, spacing=16)

        # INPUT BOXES
        # Input pemasukan
        income_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.income_amount = TextInput(hint_text='Jumlah Pemasukan (misal: 50000)', multiline=False, input_filter='int')
        self.income_desc = TextInput(hint_text='Keterangan Pemasukan', multiline=False)
        income_box.add_widget(self.income_amount)
        income_box.add_widget(self.income_desc)
        root_layout.add_widget(Label(text='Input Pemasukan:', size_hint_y=None, height=24))
        root_layout.add_widget(income_box)

        # Input pengeluaran
        expense_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.expense_amount = TextInput(hint_text='Jumlah Pengeluaran (misal: 15000)', multiline=False, input_filter='int')
        self.expense_desc = TextInput(hint_text='Keterangan Pengeluaran', multiline=False)
        expense_box.add_widget(self.expense_amount)
        expense_box.add_widget(self.expense_desc)
        root_layout.add_widget(Label(text='Input Pengeluaran:', size_hint_y=None, height=24))
        root_layout.add_widget(expense_box)

        # Buttons to add income/expense
        buttons_box = BoxLayout(size_hint_y=None, height=40, spacing=16)
        btn_add_income = Button(text='Tambahkan Pemasukan', background_color=get_color_from_hex('#10b981'))
        btn_add_income.bind(on_press=self.add_income)
        btn_add_expense = Button(text='Tambahkan Pengeluaran', background_color=get_color_from_hex('#ef4444'))
        btn_add_expense.bind(on_press=self.add_expense)
        buttons_box.add_widget(btn_add_income)
        buttons_box.add_widget(btn_add_expense)
        root_layout.add_widget(buttons_box)

        # Balance display
        self.balance_label = Label(text='Saldo Saat Ini: Rp 0', font_size=20, size_hint_y=None, height=40, bold=True)
        root_layout.add_widget(self.balance_label)

        # Riwayat transaksi dengan scrollview
        root_layout.add_widget(Label(text='Riwayat Transaksi:', size_hint_y=None, height=24))
        self.history = TransactionHistory()
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.history)
        root_layout.add_widget(scroll)

        # Load existing data
        self.load_transactions()
        self.update_balance_label()
        self.populate_history()

        return root_layout

    def add_income(self, instance):
        amount_text = self.income_amount.text.strip()
        desc_text = self.income_desc.text.strip()
        if not amount_text.isdigit() or int(amount_text) <= 0:
            self.show_error("Jumlah pemasukan harus angka positif.")
            return
        if desc_text == '':
            self.show_error("Keterangan pemasukan tidak boleh kosong.")
            return
        amount = float(amount_text)
        transaction = {
            'type': 'income',
            'amount': amount,
            'description': desc_text,
            'date': datetime.now().isoformat()
        }
        self.transactions.append(transaction)
        self.balance += amount
        self.save_transactions()
        self.update_balance_label()
        self.history.add_transaction(transaction)
        self.income_amount.text = ''
        self.income_desc.text = ''

    def add_expense(self, instance):
        amount_text = self.expense_amount.text.strip()
        desc_text = self.expense_desc.text.strip()
        if not amount_text.isdigit() or int(amount_text) <= 0:
            self.show_error("Jumlah pengeluaran harus angka positif.")
            return
        if desc_text == '':
            self.show_error("Keterangan pengeluaran tidak boleh kosong.")
            return
        amount = float(amount_text)
        if amount > self.balance:
            self.show_error("Pengeluaran melebihi saldo saat ini.")
            return
        transaction = {
            'type': 'expense',
            'amount': amount,
            'description': desc_text,
            'date': datetime.now().isoformat()
        }
        self.transactions.append(transaction)
        self.balance -= amount
        self.save_transactions()
        self.update_balance_label()
        self.history.add_transaction(transaction)
        self.expense_amount.text = ''
        self.expense_desc.text = ''

    def update_balance_label(self):
        self.balance_label.text = f"Saldo Saat Ini: Rp {self.balance:,.0f}"

    def save_transactions(self):
        try:
            with open(self.transactions_file, 'w', encoding='utf-8') as f:
                json.dump(self.transactions, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.show_error(f"Gagal menyimpan transaksi: {e}")

    def load_transactions(self):
        if os.path.exists(self.transactions_file):
            try:
                with open(self.transactions_file, 'r', encoding='utf-8') as f:
                    self.transactions = json.load(f)
                # Hitung saldo berdasarkan transaksi
                self.balance = 0
                for t in self.transactions:
                    if t.get('type') == 'income':
                        self.balance += t.get('amount',0)
                    elif t.get('type') == 'expense':
                        self.balance -= t.get('amount',0)
            except Exception as e:
                self.show_error(f"Gagal memuat data transaksi: {e}")
                self.transactions = []
                self.balance = 0

    def populate_history(self):
        self.history.clear_widgets()
        for transaction in self.transactions:
            self.history.add_transaction(transaction)

    def show_error(self, message):
        # Sederhana cetak ke console, bisa dikembangkan dialog popup
        print("ERROR:", message)

if __name__ == '__main__':
    FinanceTrackerApp().run()

