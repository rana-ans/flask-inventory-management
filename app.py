from flask import Flask, render_template, redirect, flash, request, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from datetime import datetime
from weasyprint import HTML
import io

app = Flask(__name__)

#################################
############# MYSQL #############
#################################

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Incorrect2!@localhost/POSdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = "MyK3y!"

db = SQLAlchemy(app)

#################################

def negative_check(form, field):
	if field.data < 0:
		raise ValidationError('Please enter a positive value!')

#################################

@app.route('/')
def index():
	return render_template('index.html')

#################################

@app.route('/shop')
def shop():
	return render_template('shop.html')

#################################
########### INVENTORY ###########
#################################

class Table_inventory(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	item_date = db.Column(db.DateTime, default=datetime.utcnow)
	item_image = db.Column(db.String(255), default="images/default-inventory.jpg")
	item_code = db.Column(db.String(40), nullable=False)
	item_name = db.Column(db.String(255), nullable=False)
	item_uom = db.Column(db.String(10), nullable=False)
	item_length = db.Column(db.Float(30), nullable=False)
	item_qty = db.Column(db.Integer, nullable=False)
	item_rate = db.Column(db.Float(50), nullable=False)

	# Create a String
	def __repr__(self):
		return '<name %r>' % self.item_name

class InventoryForm(FlaskForm):
	item_image = StringField("Item Image", 
				render_kw={"placeholder": "Please Enter Image Name including Extension"})
	item_code = StringField("Item Code", validators=[DataRequired()])
	item_name = StringField("Item Name", validators=[DataRequired()])
	item_uom = StringField("UoM", validators=[DataRequired()])
	item_length = FloatField("Length", validators=[DataRequired()])
	item_qty = IntegerField("Quantity", validators=[DataRequired()])
	item_rate = FloatField("Rate", validators=[DataRequired()])
	submit_item = SubmitField("Add Item to Inventory")

@app.route('/shop/inventory', methods=['GET', 'POST'])
def inventory():
	form = InventoryForm()
	if request.method == "POST":
		item_code = Table_inventory.query.filter_by(item_code=form.item_code.data).first()
		if item_code is None:
			add_item = Table_inventory(item_image=f"images/inventory/{form.item_image.data}",
				item_code=form.item_code.data, item_name=form.item_name.data, 
				item_uom=form.item_uom.data, item_length=form.item_length.data, 
				item_qty=form.item_qty.data, item_rate=form.item_rate.data)
			db.session.add(add_item)
			db.session.commit()
			form = InventoryForm(formdata=None)
			flash("Item Added Successfully!", "success")
		else:
			flash("Item Exists Already!", "warning")

	inventory = Table_inventory.query.order_by(Table_inventory.item_date)
	return render_template('inventory.html', form=form, 
							inventory=inventory)

@app.route('/shop/inventory/update/<int:id>', methods=['GET', 'POST'])
def update_inventory(id):
	form = InventoryForm()
	update_item = Table_inventory.query.get_or_404(id)
	if request.method == "POST":
		update_item.item_date = datetime.utcnow()
		update_item.item_image = request.form['item_image']
		update_item.item_code = request.form['item_code']
		update_item.item_name = request.form['item_name']
		update_item.item_uom = request.form['item_uom']
		update_item.item_length = request.form['item_length']
		update_item.item_qty = request.form['item_qty']
		update_item.item_rate = request.form['item_rate']
		try:
			db.session.commit()
			flash("Item Updated Successfully!", "success")
			return redirect(url_for("inventory"))
		except:
			flash("Error! Looks like there was an unexpected problem! Try later.", 'warning')
			return redirect(url_for("inventory"))
	else:
		return render_template("update_inventory.html", form=form, 
			update_item=update_item)

@app.route('/shop/inventory/delete/<int:id>')
def delete_item(id):
	delete_item = Table_inventory.query.get_or_404(id)
	try:
		db.session.delete(delete_item)
		db.session.commit()
		flash("Item Deleted Successfully!", "success")
		return redirect(url_for('inventory'))
	except:
		flash("An Unexpected Error Occured! Please try later!", "warning")
		return redirect(url_for('inventory'))

#################################
########### PURCHASE ############
#################################

class Table_purchase(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	item_date = db.Column(db.DateTime, default=datetime.utcnow)
	item_vendor = db.Column(db.String(150), nullable=False)
	item_code = db.Column(db.String(40), nullable=False)
	item_name = db.Column(db.String(255), nullable=False)
	item_length = db.Column(db.Float(30), nullable=False)
	item_qty = db.Column(db.Integer, nullable=False)
	item_rate = db.Column(db.Float(50), nullable=False)
	remarks = db.Column(db.String(255), nullable=True)

	# Create a String
	def __repr__(self):
		return '<name %r>' % self.item_name

class PurchaseForm(FlaskForm):
	item_vendor = StringField("Vendor", validators=[DataRequired()], 
				render_kw={"placeholder": "Please Provide Vendor Name"})
	item_codes = Table_inventory.query.order_by(Table_inventory.item_date)
	codes = [('', 'Please Select Item Code')]
	for code in item_codes:
		codes.append((code.item_code, code.item_code))
	item_code = SelectField("Item Code", choices=codes)
	item_name = StringField("Item Name", validators=[DataRequired()])
	item_length = FloatField("Length", validators=[DataRequired()])
	item_qty = IntegerField("Quantity", validators=[DataRequired()])
	item_rate = FloatField("Rate", validators=[DataRequired()])
	remarks = StringField("Remarks", render_kw={"placeholder": "Enter Remarks Here."})
	submit_item = SubmitField("Add Purchase")

@app.route('/shop/purchase', methods=['GET', 'POST'])
def purchase():
	form = PurchaseForm()
	if request.method == "POST":
		# FIRSTLY ADD ITEM IN PURCHASE
		purchase_item = Table_purchase(item_vendor=form.item_vendor.data, 
				item_code=form.item_code.data, item_name=form.item_name.data, 
				item_length=form.item_length.data, item_qty=form.item_qty.data, 
				item_rate=form.item_rate.data, remarks=form.remarks.data)
		db.session.add(purchase_item)
		# CHECK ITEM IF IT ALREADY EXISTS IN INVENTORY
		item_code = Table_inventory.query.filter_by(item_code=form.item_code.data).first()
		# UPDATE ITEM IN INVENTORY
		update_item = Table_inventory.query.get_or_404(item_code.id)
		update_item.item_date = datetime.utcnow()
		update_item.item_code = request.form['item_code']
		update_item.item_name = request.form['item_name']
		update_item.item_length = request.form['item_length']
		update_item.item_qty += int(request.form['item_qty'])
		update_item.item_rate = request.form['item_rate']
		try:
			db.session.commit()
			flash("Inventory Item - Purchase Added Successfully!", "success")
			return redirect(url_for("purchase"))
		except:
			flash("Error! Looks like there was an unexpected problem! Try later.", 'warning')
			return redirect(url_for("purchase"))
		form = InventoryForm(formdata=None)

	purchase = Table_purchase.query.order_by(Table_purchase.item_date)
	return render_template('purchase.html', form=form, 
		purchase=purchase)

@app.route('/shop/purchase/update_form', methods=['GET', 'POST'])
def update_form():
	# QUERYING DATA FROM MYSQL DB USING AJAX METHOD IN JS IN FLASK
	if request.method == "POST":
		item_code = request.form['data']
		item = Table_inventory.query.filter_by(item_code=item_code)
		item_details = {
			'id': f"{item[0].id}"
		}
		item_details['item_name'] = item[0].item_name
		item_details['item_qty'] = item[0].item_qty
		item_details['item_rate'] = item[0].item_rate
		return item_details

#################################
############# SALE ##############
#################################

class Table_sales(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sale_date = db.Column(db.DateTime, default=datetime.utcnow)
	invoice_no = db.Column(db.String(20), nullable=False)
	item_code = db.Column(db.String(40), nullable=False)
	item_name = db.Column(db.String(255), nullable=False)
	item_length = db.Column(db.Float(30), nullable=False)
	item_qty = db.Column(db.Integer, nullable=False)
	item_rate = db.Column(db.Float(50), nullable=False)

	# Create a String
	def __repr__(self):
		return '<name %r>' % self.item_name

class SaleForm(FlaskForm):
	# item_code = StringField("Item Code", validators=[DataRequired()])
	item_codes = Table_inventory.query.order_by(Table_inventory.item_date)
	codes = [('', 'Please Select Item Code')]
	for code in item_codes:
		codes.append((code.item_code, code.item_code))
	item_code = SelectField("Item Code", choices=codes)
	item_name = StringField("Item Name")
	item_length = FloatField("Length", validators=[DataRequired(), negative_check])
	item_qty = IntegerField("Quantity", validators=[DataRequired(), negative_check])
	item_rate = FloatField("Rate", validators=[DataRequired(), negative_check])
	submit = SubmitField("Add Item")

class Table_invoices(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
	customer = db.Column(db.String(20), nullable=False)
	address = db.Column(db.String(40), nullable=False)
	sale_type = db.Column(db.String(20), nullable=False)
	discount = db.Column(db.Float(10), nullable=True)
	remarks = db.Column(db.String(255), nullable=True)

	# Create a String
	def __repr__(self):
		return '<name %r>' % self.customer

class InvoiceForm(FlaskForm):
	invoice_number = StringField("Invoice #", validators=[DataRequired()])
	customer = StringField("Customer", validators=[DataRequired()], render_kw={"placeholder": "Name"})
	address = StringField("Address", validators=[DataRequired()], render_kw={"placeholder": "Address"})
	sale_type = SelectField("Sale Type", choices=[('Cash'), ('Credit')], validators=[DataRequired()])
	discount = FloatField("Discount")
	remarks = TextAreaField("Remarks", render_kw={"placeholder": "Enter Remarks Here."})
	submit = SubmitField("Generate Invoice")

@app.route('/shop/sale', methods=['GET'])
def sale():
	sales = Table_sales.query.order_by(Table_sales.sale_date)
	return render_template('sale.html', sales=sales)

@app.route('/shop/sale/add_sale/<int:id>', methods=['GET', 'POST'])
def add_sale(id):
	sale_form = SaleForm()
	invoice_form = InvoiceForm()
	from create_db import next_row_id
	invoice_no = next_row_id()
	if request.method == 'POST':
		if id == 1:
			if sale_form.item_qty.data == 0:
				flash("Item Quantity cannot be Zero!", "warning")
			else:
				add_sale = Table_sales(invoice_no=invoice_no, item_code=sale_form.item_code.data, 
					item_name=sale_form.item_name.data, item_length=sale_form.item_length.data, 
					item_qty=sale_form.item_qty.data, item_rate=sale_form.item_rate.data)
				db.session.add(add_sale)
				update_item_inventory = Table_inventory.query.filter_by(item_code=sale_form.item_code.data).first()
				update_item_inventory.item_qty -= int(sale_form.item_qty.data)
				db.session.commit()
		elif id == 2:
			add_invoice = Table_invoices(customer=invoice_form.customer.data, 
				address=invoice_form.address.data, sale_type=invoice_form.sale_type.data, 
				discount=invoice_form.discount.data, remarks=invoice_form.remarks.data)
			db.session.add(add_invoice)
			db.session.commit()
			return redirect(url_for('sale'))
		sale_form = SaleForm(formdata=None)

	sales = Table_sales.query.filter_by(invoice_no=invoice_no)
	invoices = Table_invoices.query.order_by(Table_invoices.invoice_date)
	return render_template('add_sale.html', sale_form=sale_form,
		invoice_form=invoice_form, sales=sales, invoices=invoices, 
		invoice_no=invoice_no)

@app.route('/shop/sale/update/<int:id>', methods=['GET', 'POST'])
def update_sale_entry(id):
	form = SaleForm()
	update_item = Table_sales.query.get_or_404(id)
	if request.method == "POST":
		if request.form['item_qty'] != update_item.item_qty:
			if int(request.form['item_qty']) >= int(update_item.item_qty):
				update_item_inventory = Table_inventory.query.filter_by(item_code=update_item.item_code).first()
				update_item_inventory.item_qty -= int(request.form['item_qty']) - int(update_item.item_qty)
			else:
				update_item_inventory = Table_inventory.query.filter_by(item_code=update_item.item_code).first()
				item_qty = int(update_item.item_qty) - int(request.form['item_qty'])
				update_item_inventory.item_qty += item_qty
		update_item.item_date = datetime.utcnow()
		update_item.item_length = request.form['item_length']
		update_item.item_qty = request.form['item_qty']
		update_item.item_rate = request.form['item_rate']
		try:
			db.session.commit()
			flash("Item Updated Successfully!", "success")
			return redirect(url_for("sale"))
		except:
			flash("Error! Looks like there was an unexpected problem! Try later.", 'warning')
			return redirect(url_for("sale"))
	else:
		return render_template("update_sale_item.html", form=form, 
			update_item=update_item)

@app.route('/shop/sale/delete/<int:id>')
def delete_sale_item(id):
	delete_item = Table_sales.query.get_or_404(id)
	update_item_inventory = Table_inventory.query.filter_by(item_code=delete_item.item_code).first()
	update_item_inventory.item_qty += int(delete_item.item_qty)
	try:
		db.session.delete(delete_item)
		db.session.commit()
		flash("Item Deleted Successfully!", "success")
		return redirect(url_for('sale'))
	except:
		flash("An Unexpected Error Occured! Please try later!", "warning")
		return redirect(url_for('sale'))

#################################
########### BILLINGS ############
#################################

@app.route('/shop/quote-bill')
def quote_bill():
	invoices = Table_invoices.query.order_by(Table_invoices.invoice_date)
	for invoice in invoices:
		invoice_items = Table_sales.query.filter_by(invoice_no=invoice.id).first()
		if invoice_items is None:
			delete_invoice = Table_invoices.query.get_or_404(invoice.id)
			db.session.delete(delete_invoice)
	invoices = Table_invoices.query.order_by(Table_invoices.invoice_date)
	return render_template('quote-bill.html', invoices=invoices)

@app.route('/shop/quote-bill/create_quotation/<int:id>', methods=['GET', 'POST'])
def create_quotation(id):
	invoice_type = "quotation"
	invoice = Table_invoices.query.filter_by(id=id).first()
	customer_name, customer_address = invoice.customer, invoice.address
	items = Table_sales.query.filter_by(invoice_no=invoice.id)
	if request.method == "POST":
		try:
			rendered = render_template('PDF_TEMPLATE.html', 
				invoice_type=invoice_type, invoice=invoice, 
				customer_name=customer_name, customer_address=customer_address, 
				items=items)
			html = HTML(string=rendered)
			get_pdf = html.write_pdf()
			return send_file(io.BytesIO(get_pdf), 
				attachment_filename=f'invoice_{invoice.id}.pdf')
		except Exception as e:
			flash(
			'An error occored and the pdf invoice could not be created.',
			'error')
			flash(e, 'error')

	return render_template('PDF_TEMPLATE.html', invoice_type=invoice_type, 
		invoice=invoice, customer_name=customer_name, 
		customer_address=customer_address, items=items)

@app.route('/shop/quote-bill/create_invoice/<int:id>', methods=['GET', 'POST'])
def create_invoice(id):
	invoice_type = "invoice"
	invoice = Table_invoices.query.filter_by(id=id).first()
	customer_name, customer_address = invoice.customer, invoice.address
	items = Table_sales.query.filter_by(invoice_no=invoice.id)
	if request.method == "POST":
		try:
			rendered = render_template('PDF_TEMPLATE.html', 
				invoice_type=invoice_type, invoice=invoice, 
				customer_name=customer_name, customer_address=customer_address, 
				items=items)
			html = HTML(string=rendered)
			get_pdf = html.write_pdf()
			return send_file(io.BytesIO(get_pdf), 
				attachment_filename=f'invoice_{invoice.id}.pdf')
		except Exception as e:
			flash(
			'An error occored and the pdf invoice could not be created.',
			'error')
			flash(e, 'error')

	return render_template('PDF_TEMPLATE.html', invoice_type=invoice_type, 
		invoice=invoice, customer_name=customer_name, 
		customer_address=customer_address, items=items)

@app.route('/quote-bill/update-invoice-details/<int:id>', methods=['GET', 'POST'])
def update_invoice_details(id):
	form = InvoiceForm()
	update_invoice = Table_invoices.query.get_or_404(id)
	if request.method == "POST":
		update_invoice.invoice_date = datetime.utcnow()
		update_invoice.customer = request.form['customer']
		update_invoice.sale_type = request.form['sale_type']
		update_invoice.discount = request.form['discount']
		update_invoice.remarks = request.form['remarks']
		try:
			db.session.commit()
			flash("Invoice Updated Successfully!", "success")
			return redirect(url_for("quote_bill"))
		except:
			flash("Error! Looks like there was an unexpected problem! Try later.", 'warning')
			return redirect(url_for("quote_bill"))

	sales = Table_sales.query.filter_by(invoice_no=id)
	return render_template("update_invoice_details.html", form=form, 
			update_invoice=update_invoice, sales=sales)

@app.route('/shop/quote-bill/delete/<int:id>')
def delete_invoice(id):
	delete_item = Table_invoices.query.get_or_404(id)
	try:
		db.session.delete(delete_item)
		db.session.commit()
		flash("Item Deleted Successfully!", "success")
		return redirect(url_for('quote_bill'))
	except:
		flash("An Unexpected Error Occured! Please try later!", "warning")
		return redirect(url_for('quote_bill'))

#################################
########### ACCOUNTS ############
#################################

class Table_accounts(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	dated = db.Column(db.DateTime, default=datetime.utcnow)
	bank_account = db.Column(db.String(50), nullable=False)
	payer = db.Column(db.String(40), nullable=False)
	beneficiary = db.Column(db.String(40), nullable=False)
	description = db.Column(db.String(255), nullable=False)
	debit = db.Column(db.Float(30), default=0.0, nullable=False)
	credit = db.Column(db.Float(30), default=0.0, nullable=False)
	tx_tax = db.Column(db.Float(15), default=0.0, nullable=False)

	# Create a String
	def __repr__(self):
		return '<name %r>' % self.bank_account
# Table_accounts(bank_account='', payer='', beneficiary='', description='', debit=, credit=, tx_tax=)

class AccountsForm(FlaskForm):
	bank_accounts = [
		('', 'Please Select Bank Account'), 
		('SELF MEZN', 'SELF MEZN'), 
		('UHUD MEZN', 'UHUD MEZN'), 
		('SELF JC', 'SELF JC'), 
		('SELF BAHL', 'SELF BAHL')
	]
	bank_account = SelectField("Bank Accounts", choices=bank_accounts)
	payer = StringField("Payer")
	beneficiary = StringField("Beneficiary", validators=[DataRequired()])
	description = StringField("Description", validators=[DataRequired()])
	debit = FloatField("Debit", validators=[DataRequired(), negative_check])
	credit = FloatField("Credit", validators=[DataRequired(), negative_check])
	tx_tax = FloatField("TX_Tax", validators=[DataRequired(), negative_check])
	submit = SubmitField("Add Details")

@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
	form = AccountsForm()
	if request.method == 'POST':
		if form.bank_account.data == '':
			flash("Please Select a Bank Account!", "warning")
		elif '/' in form.payer.data or '/' in form.beneficiary.data:
			flash("Please avoid Symbols '/' in Payer or Beneficiary Details", "warning")
		else:
			add_details = Table_accounts(bank_account=form.bank_account.data, 
				payer=form.payer.data, beneficiary=form.beneficiary.data, 
				description=form.description.data, debit=form.debit.data, 
				credit=form.credit.data, tx_tax=form.tx_tax.data)
			db.session.add(add_details)
			db.session.commit()
			form = AccountsForm(formdata=None)
	details = Table_accounts.query.order_by(Table_accounts.dated)
	return render_template('accounts.html', form=form, 
		details=details)

@app.route('/account_details/<int:uid>/<account_title>/<bank_account>')
def account_details(uid, account_title, bank_account):
	if uid == 1:
		details = Table_accounts.query.filter_by(bank_account=account_title)
	elif uid == 2 or uid == 3:
		details = Table_accounts.query.filter(and_(Table_accounts.bank_account==bank_account, or_(Table_accounts.payer==account_title, Table_accounts.beneficiary==account_title)))

	return render_template('account_details.html', details=details, 
		account_title=account_title)

#################################

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

#################################

@app.errorhandler(500)
def page_not_found(e):
	return render_template('500.html'), 500

#################################

#################################
# inventory >>> InventoryUID, date, image, product code, product name, UOM, length, qty, rate
# purchase >>> PurchaseUID, date, vendor, type, InventoryUID, product code, product name, length, qty, rate, remarks
# GRN >>> GRNUID, date, vendor, type, InventoryUID, product code, product name, length, qty, rate, remarks
# sale >>> SaleUID, date, customer, type(credit, cash), InventoryUID, product code, product name, length, qty, rate, discount, remarks
# credit >>> CreditUID, date, customer, InventoryUID, product code, product name, length, qty, rate
# party ledger >>> PartyUID, date, party name, item_rate, debit, credit
# stock issuance >>> StockissueUID, date, InventoryUID, product code, product name, length, qty
# quotation >>> QuotationUID, date, customer, type, InventoryUID, product code, product name, length, qty, rate, discount
# bill >>> BillUID, date, customer, type, InventoryUID, product code, product name, length, qty, rate, discount
# ideas for filtering products: pop-up window.
#################################
