import mysql.connector

mydb = mysql.connector.connect(
	host="YOUR HOST NAME",
	user="YOUR ROOT USER NAME",
	passwd="YOUR PASSWORD", 
	database="YOUR DATABASE NAME"
	)

my_cursor = mydb.cursor()

# GETTING NEXT ROW ID IN A TABLE
def next_row_id():
	my_cursor.execute("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='posdb' AND TABLE_NAME='Table_invoices'")
	return my_cursor.fetchone()[0]

def create_all_tables():
	from app import db
	db.create_all()
	print("ALL DEFINED TABLES WERE CREATED!")


# DELETING DB
# my_cursor.execute("DROP DATABASE IF EXISTS ProjectDetails")

# my_cursor.execute("SHOW DATABASES")
# my_cursor.execute("DROP TABLE Returned")
# my_cursor.execute("CREATE TABLE inventory (id INT AUTO_INCREMENT PRIMARY KEY, update_date DATE, image VARCHAR(255), product_code VARCHAR(30), product_name VARCHAR(150), uom VARCHAR(10), length FLOAT(24), quantity INT(20), rate FLOAT(24))")
# my_cursor.execute("INSERT INTO projects (name, address) VALUES (%s, %s)", ("Ans", "115-Cooper Road"))
# my_cursor.execute("SELECT * FROM Inventory")
# my_cursor.execute("SHOW COLUMNS FROM POSdb.inventory")

# my_cursor.execute("DROP TABLE Table_accounts")
# my_cursor.execute("DROP TABLE Table_invoices")
# my_cursor.execute("SHOW TABLES")

# result = next_row_id()
# result = filter_db('ans', 'ans')
# print(result)

if __name__=="__main__":
	for data in my_cursor:
		print(data)
