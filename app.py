from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB Atlas Connection
app.config["MONGO_URI"] = "mongodb+srv://kreddy0597:kreddy0597@cluster0.fpkka.mongodb.net/farmlink?retryWrites=true&w=majority"
mongo = PyMongo(app)
db = mongo.db

# Ensure collections exist
if "users" not in db.list_collection_names():
    db.create_collection("users")
if "products" not in db.list_collection_names():
    db.create_collection("products")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_type = request.form["user_type"]
        username = request.form["username"]
        password = request.form["password"]

        if db.users.find_one({"username": username}):
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        db.users.insert_one({"username": username, "password": hashed_password, "user_type": user_type})
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.users.find_one({"username": username})

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["user_type"] = user["user_type"]
            flash("Login successful!", "success")

            return redirect(url_for("farmer_dashboard" if user["user_type"] == "farmer" else "buyer_dashboard"))

        flash("Invalid credentials!", "danger")

    return render_template("login.html")


@app.route("/farmer_dashboard")
def farmer_dashboard():
    if "username" not in session or session["user_type"] != "farmer":
        return redirect(url_for("login"))

    products = db.products.find({"farmer": session["username"]})
    return render_template("farmer_dashboard.html", products=products)


@app.route("/add_produce", methods=["GET", "POST"])
def add_produce():
    if "username" not in session or session["user_type"] != "farmer":
        return redirect(url_for("login"))

    if request.method == "POST":
        product_name = request.form["product_name"]
        price = request.form["price"]
        quantity = request.form["quantity"]

        db.products.insert_one({
            "product_name": product_name,
            "price": price,
            "quantity": quantity,
            "farmer": session["username"]
        })

        flash("Product added successfully!", "success")
        return redirect(url_for("farmer_dashboard"))

    return render_template("add_produce.html")


@app.route("/buyer_dashboard")
def buyer_dashboard():
    if "username" not in session or session["user_type"] != "buyer":
        return redirect(url_for("login"))

    products = db.products.find()
    return render_template("buyer_dashboard.html", products=products)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Use an available port

