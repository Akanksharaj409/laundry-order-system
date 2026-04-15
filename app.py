import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# In-memory storage
orders = []

# Hardcoded prices (INR)
PRICES = {
    "Shirt": 50,
    "Pants": 60,
    "Saree": 100,
    "Dress": 80,
    "Kurta": 70,
    "Blouse": 40
}

# Complete interactive HTML + JS frontend (single file)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🧺 Laundry Order System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        .garment-row { margin-bottom: 8px; }
        .badge { font-size: 0.9em; }
    </style>
</head>
<body class="bg-light">
<div class="container mt-4">
    <h1 class="text-center mb-4">🧺 Mini Laundry Order Management</h1>
    
    <ul class="nav nav-tabs mb-4" id="mainTabs" role="tablist">
        <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#createTab">Create Order</button></li>
        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#ordersTab" onclick="loadOrders()">View Orders</button></li>
        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#dashboardTab" onclick="loadDashboard()">Dashboard</button></li>
    </ul>

    <div class="tab-content">
        <!-- CREATE ORDER -->
        <div class="tab-pane fade show active" id="createTab">
            <div class="card">
                <div class="card-body">
                    <form id="orderForm">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Customer Name</label>
                                <input type="text" class="form-control" id="customer_name" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Phone Number</label>
                                <input type="tel" class="form-control" id="phone" required>
                            </div>
                        </div>

                        <label class="form-label">Garments</label>
                        <div id="garmentsContainer"></div>
                        <button type="button" class="btn btn-secondary btn-sm mt-2" onclick="addGarmentField()">+ Add Garment</button>

                        <button type="button" class="btn btn-success mt-4 w-100" onclick="createOrder()">Create Order & Get Bill</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- VIEW ORDERS -->
        <div class="tab-pane fade" id="ordersTab">
            <div class="row g-3 mb-3">
                <div class="col-md-3">
                    <input type="text" id="filter_status" class="form-control" placeholder="Status" onkeyup="if(event.keyCode===13) loadOrders()">
                </div>
                <div class="col-md-3">
                    <input type="text" id="filter_name" class="form-control" placeholder="Customer Name" onkeyup="if(event.keyCode===13) loadOrders()">
                </div>
                <div class="col-md-3">
                    <input type="text" id="filter_phone" class="form-control" placeholder="Phone" onkeyup="if(event.keyCode===13) loadOrders()">
                </div>
                <div class="col-md-3 d-flex gap-2">
                    <button class="btn btn-primary flex-fill" onclick="loadOrders()">Filter</button>
                    <button class="btn btn-outline-secondary flex-fill" onclick="clearFilters()">Clear</button>
                </div>
            </div>

            <table class="table table-hover table-striped" id="ordersTable">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Customer</th>
                        <th>Phone</th>
                        <th>Garments</th>
                        <th>Total (₹)</th>
                        <th>Status</th>
                        <th>Est. Delivery</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>

        <!-- DASHBOARD -->
        <div class="tab-pane fade" id="dashboardTab">
            <div class="row" id="dashboardCards"></div>
        </div>
    </div>
</div>

<script>
    function addGarmentField() {
        const container = document.getElementById('garmentsContainer');
        const div = document.createElement('div');
        div.className = 'input-group garment-row';
        div.innerHTML = `
            <select class="form-select garment-type" style="max-width:220px">
                <option value="Shirt">Shirt</option>
                <option value="Pants">Pants</option>
                <option value="Saree">Saree</option>
                <option value="Dress">Dress</option>
                <option value="Kurta">Kurta</option>
                <option value="Blouse">Blouse</option>
            </select>
            <input type="number" class="form-control garment-qty" value="1" min="1" style="max-width:100px">
            <button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">×</button>
        `;
        container.appendChild(div);
    }

    window.onload = () => addGarmentField();

    async function createOrder() {
        const customer_name = document.getElementById('customer_name').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const garmentRows = document.querySelectorAll('.garment-row');
        
        const garments = Array.from(garmentRows).map(row => ({
            type: row.querySelector('.garment-type').value,
            quantity: parseInt(row.querySelector('.garment-qty').value)
        })).filter(g => g.quantity > 0);

        if (!customer_name || !phone || garments.length === 0) {
            alert("Please fill all fields and add at least one garment");
            return;
        }

        const res = await fetch('/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ customer_name, phone, garments })
        });

        const data = await res.json();
        if (res.ok) {
            alert(`✅ Order Created!\nID: ${data.id}\nTotal Bill: ₹${data.total_bill}\nEst. Delivery: ${new Date(data.estimated_delivery).toLocaleDateString()}`);
            document.getElementById('orderForm').reset();
            document.getElementById('garmentsContainer').innerHTML = '';
            addGarmentField();
            // Switch to orders tab
            document.querySelector('[data-bs-target="#ordersTab"]').click();
            loadOrders();
        } else {
            alert("Error: " + JSON.stringify(data));
        }
    }

    async function loadOrders() {
        let url = '/orders?';
        const status = document.getElementById('filter_status').value.trim();
        const name = document.getElementById('filter_name').value.trim();
        const phone = document.getElementById('filter_phone').value.trim();
        if (status) url += `status=${encodeURIComponent(status)}&`;
        if (name) url += `customer_name=${encodeURIComponent(name)}&`;
        if (phone) url += `phone=${encodeURIComponent(phone)}&`;

        const res = await fetch(url);
        const data = await res.json();

        const tbody = document.querySelector('#ordersTable tbody');
        tbody.innerHTML = '';

        data.forEach(order => {
            const garmentsStr = order.garments.map(g => `${g.type}×${g.quantity}`).join(', ');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><small>${order.id.substring(0,8)}…</small></td>
                <td>${order.customer_name}</td>
                <td>${order.phone}</td>
                <td>${garmentsStr}</td>
                <td class="fw-bold">₹${order.total_bill}</td>
                <td><span class="badge bg-${getBadge(order.status)}">${order.status}</span></td>
                <td>${new Date(order.estimated_delivery).toLocaleDateString()}</td>
                <td>
                    <select class="form-select form-select-sm" onchange="updateStatus('${order.id}', this.value)" style="width:140px">
                        <option value="RECEIVED" ${order.status==='RECEIVED'?'selected':''}>RECEIVED</option>
                        <option value="PROCESSING" ${order.status==='PROCESSING'?'selected':''}>PROCESSING</option>
                        <option value="READY" ${order.status==='READY'?'selected':''}>READY</option>
                        <option value="DELIVERED" ${order.status==='DELIVERED'?'selected':''}>DELIVERED</option>
                    </select>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    function getBadge(status) {
        if (status === 'RECEIVED') return 'primary';
        if (status === 'PROCESSING') return 'warning';
        if (status === 'READY') return 'info';
        return 'success';
    }

    async function updateStatus(id, status) {
        await fetch(`/orders/${id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        loadOrders();
    }

    function clearFilters() {
        document.getElementById('filter_status').value = '';
        document.getElementById('filter_name').value = '';
        document.getElementById('filter_phone').value = '';
        loadOrders();
    }

    async function loadDashboard() {
        const res = await fetch('/dashboard');
        const data = await res.json();
        const container = document.getElementById('dashboardCards');
        container.innerHTML = `
            <div class="col-md-4 mb-3">
                <div class="card text-center h-100">
                    <div class="card-body">
                        <h5>Total Orders</h5>
                        <h1 class="text-primary">${data.total_orders}</h1>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card text-center h-100">
                    <div class="card-body">
                        <h5>Total Revenue</h5>
                        <h1 class="text-success">₹${data.total_revenue}</h1>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5>Orders by Status</h5>
                        <ul class="list-group list-group-flush">
                            ${Object.entries(data.orders_per_status).map(([s, c]) => `
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>${s}</span><span class="badge bg-secondary">${c}</span>
                                </li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    customer_name = data.get('customer_name')
    phone = data.get('phone')
    garments = data.get('garments', [])

    total_bill = sum(PRICES.get(g['type'], 0) * g.get('quantity', 0) for g in garments)

    order = {
        "id": str(uuid.uuid4()),
        "customer_name": customer_name,
        "phone": phone,
        "garments": garments,
        "total_bill": total_bill,
        "status": "RECEIVED",
        "estimated_delivery": (datetime.now() + timedelta(days=3)).isoformat(),
        "created_at": datetime.now().isoformat()
    }
    orders.append(order)
    return jsonify(order), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    status = request.args.get('status')
    name = request.args.get('customer_name')
    phone = request.args.get('phone')

    result = orders[:]
    if status:
        result = [o for o in result if o['status'] == status.upper()]
    if name:
        result = [o for o in result if name.lower() in o['customer_name'].lower()]
    if phone:
        result = [o for o in result if phone in o['phone']]
    return jsonify(result)

@app.route('/orders/<string:order_id>/status', methods=['PATCH'])
def update_status(order_id):
    data = request.get_json()
    status = data.get('status')
    for order in orders:
        if order['id'] == order_id:
            order['status'] = status
            return jsonify(order)
    return jsonify({"error": "Order not found"}), 404

@app.route('/dashboard', methods=['GET'])
def dashboard():
    total_orders = len(orders)
    total_revenue = sum(o['total_bill'] for o in orders)
    status_count = {}
    for o in orders:
        status_count[o['status']] = status_count.get(o['status'], 0) + 1
    return jsonify({
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "orders_per_status": status_count
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
