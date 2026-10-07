from flask import Flask, render_template, session, redirect, url_for, request

app = Flask(__name__)
app.secret_key = "smartcart-project-secret"

BUDGET_DEFAULT = 2000


# =========================
# PRODUCTS
# =========================

PRODUCTS = [
    {
        "id": 1,
        "name": "Milk",
        "price": 35,
        "category": "Groceries",
        "emoji": "🥛",
        "location": "Aisle 1",
        "alt": "Curd"
    },
    {
        "id": 2,
        "name": "Brown Bread",
        "price": 40,
        "category": "Groceries",
        "emoji": "🍞",
        "location": "Aisle 2",
        "alt": "White Bread"
    },
    {
        "id": 3,
        "name": "Basmati Rice",
        "price": 180,
        "category": "Groceries",
        "emoji": "🍚",
        "location": "Aisle 3",
        "alt": "Sona Masoori Rice"
    },
    {
        "id": 4,
        "name": "Oreo",
        "price": 50,
        "category": "Snacks",
        "emoji": "🍪",
        "location": "Aisle 4",
        "alt": "Marie Biscuit"
    },
    {
        "id": 5,
        "name": "Shampoo",
        "price": 210,
        "category": "Personal Care",
        "emoji": "🧴",
        "location": "Aisle 5",
        "alt": "Herbal Shampoo"
    },
    {
        "id": 6,
        "name": "Bath Soap",
        "price": 45,
        "category": "Personal Care",
        "emoji": "🧼",
        "location": "Aisle 5",
        "alt": "Value Soap"
    },
    {
        "id": 7,
        "name": "Pasta",
        "price": 75,
        "category": "Groceries",
        "emoji": "🍝",
        "location": "Aisle 3",
        "alt": "Macaroni"
    },
    {
        "id": 8,
        "name": "Pasta Sauce",
        "price": 120,
        "category": "Groceries",
        "emoji": "🍅",
        "location": "Aisle 3",
        "alt": "Tomato Puree"
    },
    {
        "id": 9,
        "name": "Cheese",
        "price": 95,
        "category": "Dairy",
        "emoji": "🧀",
        "location": "Aisle 1",
        "alt": "Cheese Spread"
    },
    {
        "id": 10,
        "name": "Juice",
        "price": 90,
        "category": "Beverages",
        "emoji": "🧃",
        "location": "Aisle 6",
        "alt": "Lemon Drink"
    }
]

PRODUCT_BY_ID = {
    p["id"]: p for p in PRODUCTS
}


# =========================
# CART FUNCTIONS
# =========================

def get_cart():
    return session.get("cart", {})


def cart_items():
    items = []

    for pid, qty in get_cart().items():

        product = PRODUCT_BY_ID.get(int(pid))

        if product and qty > 0:

            item = dict(product)

            item["qty"] = qty

            item["line_total"] = product["price"] * qty

            items.append(item)

    return items


def cart_total():
    return sum(
        item["line_total"]
        for item in cart_items()
    )


def cart_count():
    return sum(
        item["qty"]
        for item in cart_items()
    )


# =========================
# BUDGET
# =========================

def get_budget():
    return session.get(
        "budget",
        BUDGET_DEFAULT
    )


def budget_status():

    total = cart_total()
    budget = get_budget()

    # Budget exceeded
    if total > budget:

        return {
            "status": "danger",
            "message": "⚠️ Budget exceeded! Consider removing some items."
        }

    # Percentage used
    percentage = (
        (total / budget) * 100
        if budget > 0
        else 0
    )

    # More than 80%
    if percentage >= 80:

        return {
            "status": "warning",
            "message": "⚠️ You have used more than 80% of your budget."
        }

    # Safe
    return {
        "status": "safe",
        "message": "✅ You are within your shopping budget."
    }


# =========================
# SMART RECOMMENDATIONS
# =========================

def recommendations():

    ids = {
        item["id"]
        for item in cart_items()
    }

    recommendations_list = []

    pairs = {

        # Pasta → sauce and cheese
        7: [8, 9],

        # Milk → bread
        1: [2],

        # Rice → milk and pasta
        3: [1, 7],

        # Shampoo → soap
        5: [6]
    }

    for pid in ids:

        for rid in pairs.get(pid, []):

            if (
                rid not in ids
                and rid in PRODUCT_BY_ID
                and rid not in [
                    r["id"]
                    for r in recommendations_list
                ]
            ):

                recommendations_list.append(
                    PRODUCT_BY_ID[rid]
                )

    # If no specific recommendations,
    # show three useful products
    if not recommendations_list:

        for product in PRODUCTS:

            if product["id"] not in ids:

                recommendations_list.append(product)

            if len(recommendations_list) == 3:
                break

    return recommendations_list[:3]


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    total = cart_total()
    budget = get_budget()

    return render_template(

        "dashboard.html",

        cart_count=cart_count(),

        total=total,

        budget=budget,

        remaining=budget - total,

        recommendation_count=len(
            recommendations()
        ),

        # IMPORTANT:
        # This fixes the budget_status error
        budget_status=budget_status()
    )


# =========================
# PRODUCTS
# =========================

@app.route("/products")
def products():

    return render_template(

        "products.html",

        products=PRODUCTS,

        cart_count=cart_count()
    )


# =========================
# ADD TO CART
# =========================

@app.route("/add/<int:product_id>")
def add_to_cart(product_id):

    if product_id in PRODUCT_BY_ID:

        cart = get_cart()

        key = str(product_id)

        cart[key] = cart.get(key, 0) + 1

        session["cart"] = cart

        session.modified = True

    return redirect(
        request.referrer
        or url_for("products")
    )


# =========================
# REMOVE FROM CART
# =========================

@app.route("/remove/<int:product_id>")
def remove_from_cart(product_id):

    cart = get_cart()

    key = str(product_id)

    if key in cart:

        cart[key] -= 1

        if cart[key] <= 0:

            del cart[key]

    session["cart"] = cart

    session.modified = True

    return redirect(
        url_for("cart")
    )


# =========================
# CART
# =========================

@app.route("/cart")
def cart():

    total = cart_total()

    budget = get_budget()

    return render_template(

        "cart.html",

        items=cart_items(),

        total=total,

        budget=budget,

        remaining=budget - total,

        budget_status=budget_status()
    )


# =========================
# BUDGET
# =========================

@app.route(
    "/budget",
    methods=["GET", "POST"]
)
def budget():

    if request.method == "POST":

        try:

            value = float(
                request.form.get(
                    "budget",
                    BUDGET_DEFAULT
                )
            )

            if value > 0:

                session["budget"] = value

        except (
            TypeError,
            ValueError
        ):

            pass

        return redirect(
            url_for("budget")
        )

    current_budget = get_budget()

    total = cart_total()

    return render_template(

        "budget.html",

        budget=current_budget,

        total=total,

        remaining=current_budget - total,

        budget_status=budget_status()
    )


# =========================
# RECOMMENDATIONS
# =========================

@app.route("/recommendations")
def smart_recommendations():

    return render_template(

        "recommendations.html",

        recommendations=recommendations(),

        total=cart_total()
    )


# =========================
# STORE MAP
# =========================

@app.route("/store-map")
def store_map():

    return render_template(

        "store_map.html",

        products=PRODUCTS
    )


# =========================
# CHECKOUT
# =========================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    items = cart_items()

    total = cart_total()

    budget = get_budget()

    # 5% discount if total >= ₹500
    discount = (
        round(total * 0.05, 2)
        if total >= 500
        else 0
    )

    final_total = round(
        total - discount,
        2
    )

    # Complete purchase
    if request.method == "POST" and items:

        history = session.get(
            "history",
            []
        )

        history.append({

            "items": items,

            "subtotal": total,

            "discount": discount,

            "total": final_total
        })

        session["history"] = history

        # Empty cart
        session["cart"] = {}

        return render_template(

            "checkout.html",

            items=items,

            subtotal=total,

            discount=discount,

            final_total=final_total,

            completed=True
        )

    return render_template(

        "checkout.html",

        items=items,

        subtotal=total,

        discount=discount,

        final_total=final_total,

        budget=budget,

        completed=False
    )


# =========================
# ANALYTICS
# =========================

@app.route("/analytics")
def analytics():

    history = session.get(
        "history",
        []
    )

    category_totals = {}

    total_spent = 0

    total_saved = 0

    total_items = 0

    for order in history:

        total_spent += order["total"]

        total_saved += order["discount"]

        for item in order["items"]:

            total_items += item["qty"]

            category = item["category"]

            category_totals[category] = (
                category_totals.get(
                    category,
                    0
                )
                + item["line_total"]
            )

    return render_template(

        "analytics.html",

        history=history,

        category_totals=category_totals,

        total_spent=round(
            total_spent,
            2
        ),

        total_saved=round(
            total_saved,
            2
        ),

        total_items=total_items
    )


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )
