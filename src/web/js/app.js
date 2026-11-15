// Electronics Vendor Web Application - Frontend JavaScript
// Backend API endpoint (adjust as needed)
const API_BASE = 'http://localhost:5000/api';

let cart = JSON.parse(localStorage.getItem('cart')) || [];

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadCategories();
    loadManufacturers();
    updateCartDisplay();
    
    // Setup navigation
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = link.getAttribute('href').substring(1);
            showSection(target);
        });
    });
    
    // Setup checkout form
    document.getElementById('checkout-form').addEventListener('submit', handleCheckout);
});

// Load products from backend
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE}/products`);
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('products-grid').innerHTML = 
            '<p class="error">Error loading products. Please check if the backend server is running.</p>';
    }
}

// Load categories for filter
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        const categories = await response.json();
        const select = document.getElementById('category-filter');
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.category_id;
            option.textContent = cat.category_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load manufacturers for filter
async function loadManufacturers() {
    try {
        const response = await fetch(`${API_BASE}/manufacturers`);
        const manufacturers = await response.json();
        const select = document.getElementById('manufacturer-filter');
        manufacturers.forEach(mfg => {
            const option = document.createElement('option');
            option.value = mfg;
            option.textContent = mfg;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading manufacturers:', error);
    }
}

// Display products in grid
function displayProducts(products) {
    const grid = document.getElementById('products-grid');
    if (products.length === 0) {
        grid.innerHTML = '<p>No products found.</p>';
        return;
    }
    
    grid.innerHTML = products.map(product => `
        <div class="product-card">
            <h3>${product.product_name}</h3>
            <div class="manufacturer">${product.manufacturer || 'Unknown'}</div>
            <div class="price">$${parseFloat(product.price).toFixed(2)}</div>
            <div class="description">${product.description || 'No description available'}</div>
            <button onclick="addToCart(${product.product_id}, '${product.product_name}', ${product.price})">
                Add to Cart
            </button>
        </div>
    `).join('');
}

// Filter products
async function filterProducts() {
    const category = document.getElementById('category-filter').value;
    const manufacturer = document.getElementById('manufacturer-filter').value;
    const search = document.getElementById('search-box').value;
    
    let url = `${API_BASE}/products?`;
    const params = [];
    if (category) params.push(`category=${category}`);
    if (manufacturer) params.push(`manufacturer=${encodeURIComponent(manufacturer)}`);
    if (search) params.push(`search=${encodeURIComponent(search)}`);
    
    if (params.length > 0) {
        url += params.join('&');
    }
    
    try {
        const response = await fetch(url);
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        console.error('Error filtering products:', error);
    }
}

// Add product to cart
function addToCart(productId, productName, price) {
    const existingItem = cart.find(item => item.product_id === productId);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            product_id: productId,
            product_name: productName,
            price: price,
            quantity: 1
        });
    }
    saveCart();
    updateCartDisplay();
    showMessage('Product added to cart!', 'success');
}

// Remove item from cart
function removeFromCart(productId) {
    cart = cart.filter(item => item.product_id !== productId);
    saveCart();
    updateCartDisplay();
}

// Update cart quantity
function updateCartQuantity(productId, change) {
    const item = cart.find(item => item.product_id === productId);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(productId);
        } else {
            saveCart();
            updateCartDisplay();
        }
    }
}

// Save cart to localStorage
function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

// Update cart display
function updateCartDisplay() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById('cart-count').textContent = count;
    
    const cartItems = document.getElementById('cart-items');
    if (cart.length === 0) {
        cartItems.innerHTML = '<p>Your cart is empty.</p>';
        document.getElementById('cart-total').textContent = '0.00';
    } else {
        cartItems.innerHTML = cart.map(item => `
            <div class="cart-item">
                <div class="cart-item-info">
                    <strong>${item.product_name}</strong>
                    <div>$${parseFloat(item.price).toFixed(2)} x ${item.quantity}</div>
                </div>
                <div class="cart-item-controls">
                    <button onclick="updateCartQuantity(${item.product_id}, -1)">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateCartQuantity(${item.product_id}, 1)">+</button>
                    <button onclick="removeFromCart(${item.product_id})">Remove</button>
                </div>
            </div>
        `).join('');
        
        const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        document.getElementById('cart-total').textContent = total.toFixed(2);
    }
}

// Show section
function showSection(sectionId) {
    document.querySelectorAll('section').forEach(section => {
        section.style.display = 'none';
    });
    
    if (sectionId === 'cart') {
        document.getElementById('cart').style.display = 'block';
    } else if (sectionId === 'orders') {
        document.getElementById('orders').style.display = 'block';
    } else {
        document.getElementById('products').style.display = 'block';
    }
}

// Checkout
function checkout() {
    if (cart.length === 0) {
        showMessage('Your cart is empty!', 'error');
        return;
    }
    showSection('checkout');
}

// Handle checkout form submission
async function handleCheckout(e) {
    e.preventDefault();
    
    const orderData = {
        customer: {
            email: document.getElementById('customer-email').value,
            first_name: document.getElementById('customer-firstname').value,
            last_name: document.getElementById('customer-lastname').value,
            phone: document.getElementById('customer-phone').value,
            customer_type: 'regular',
            credit_card_number: document.getElementById('credit-card').value,
            credit_card_expiry: document.getElementById('card-expiry').value,
            credit_card_cvv: document.getElementById('card-cvv').value
        },
        shipping_address: {
            address: document.getElementById('shipping-address').value,
            city: document.getElementById('shipping-city').value,
            state: document.getElementById('shipping-state').value,
            zip_code: document.getElementById('shipping-zip').value
        },
        items: cart
    };
    
    try {
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage(`Order placed successfully! Order ID: ${result.order_id}`, 'success');
            cart = [];
            saveCart();
            updateCartDisplay();
            document.getElementById('checkout-form').reset();
            showSection('products');
        } else {
            showMessage(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showMessage('Error placing order. Please try again.', 'error');
    }
}

// Load orders for customer
async function loadOrders() {
    const email = document.getElementById('order-email').value;
    if (!email) {
        showMessage('Please enter your email address.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/orders?email=${encodeURIComponent(email)}`);
        const orders = await response.json();
        displayOrders(orders);
    } catch (error) {
        console.error('Error loading orders:', error);
        showMessage('Error loading orders. Please try again.', 'error');
    }
}

// Display orders
function displayOrders(orders) {
    const ordersList = document.getElementById('orders-list');
    if (orders.length === 0) {
        ordersList.innerHTML = '<p>No orders found for this email.</p>';
        return;
    }
    
    ordersList.innerHTML = orders.map(order => `
        <div class="order-card">
            <h3>Order #${order.order_id}</h3>
            <div class="order-info">
                Date: ${new Date(order.order_date).toLocaleDateString()}<br>
                Status: ${order.status}<br>
                Type: ${order.order_type}
            </div>
            <div class="order-total">Total: $${parseFloat(order.total_amount).toFixed(2)}</div>
        </div>
    `).join('');
}

// Show message
function showMessage(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    const main = document.querySelector('main');
    main.insertBefore(messageDiv, main.firstChild);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Make functions available globally
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateCartQuantity = updateCartQuantity;
window.filterProducts = filterProducts;
window.checkout = checkout;
window.loadOrders = loadOrders;


