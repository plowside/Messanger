import json, os
	
class FakeDatabase:
	def __init__(self):
		self.data = {}  # Имитация таблицы в базе данных

	def execute(self, query, parameters=None):
		# Эмулируем выполнение SQL-запросов
		if query.startswith("CREATE TABLE"):
			table_name = query.split()[-1]
			self.data[table_name] = []

		elif query.startswith("INSERT INTO"):
			table_name = query.split()[2]
			values = parameters
			self.data[table_name].append(values)

		elif query.startswith("SELECT * FROM"):
			table_name = query.split()[-1]
			return self.data.get(table_name, [])

		elif query.startswith("DELETE FROM"):
			table_name = query.split()[2]
			self.data[table_name] = []

		else:
			raise ValueError("Unsupported query")

	def commit(self):
		# Эмулируем сохранение изменений, но в памяти это не требуется
		pass

con = FakeDatabase()
cur = con
cur.execute("CREATE TABLE users")

if __name__ == '__main__':
	# Пример использования
	db = FakeDatabase()

	# Вставка данных
	db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["Alice", 30])
	db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["Bob", 25])

	# Выполнение SELECT-запроса
	result = db.execute("SELECT * FROM users")
	print(result)  # Вывод данных из таблицы users

	# Очистка таблицы
	db.execute("DELETE FROM users")

	# Повторное SELECT
	result = db.execute("SELECT * FROM users")
	print(result)  # Должен вывести пустой список