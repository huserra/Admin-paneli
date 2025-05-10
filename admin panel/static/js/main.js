// Initialize charts
function initializeCharts() {
    // User Chart
    new Chart(document.getElementById('userChart').getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Active Users', 'Passive Users'],
            datasets: [{
                data: [80, 20],
                backgroundColor: ['#007bff', '#ffc107']
            }]
        }
    });

    // Locker Chart
    new Chart(document.getElementById('lockerChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Full', 'Empty'],
            datasets: [{
                data: [60, 40],
                backgroundColor: ['#28a745', '#dc3545']
            }]
        }
    });

    // Payment Chart
    new Chart(document.getElementById('paymentChart').getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Completed', 'Pending', 'Cancelled'],
            datasets: [{
                data: [70, 20, 10],
                backgroundColor: ['#17a2b8', '#ffc107', '#dc3545']
            }]
        }
    });
}

// Search Functions
function filterTable(tableId, searchId) {
    const searchText = document.getElementById(searchId).value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = false;

        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell.textContent.toLowerCase().includes(searchText)) {
                found = true;
                break;
            }
        }

        row.style.display = found ? '' : 'none';
    }
}

// Initialize search listeners
function initializeSearchListeners() {
    document.getElementById('userSearch')?.addEventListener('input', () => filterTable('userTableBody', 'userSearch'));
    document.getElementById('lockerSearch')?.addEventListener('input', () => filterTable('lockerTableBody', 'lockerSearch'));
    document.getElementById('reservationSearch')?.addEventListener('input', () => filterTable('reservationTableBody', 'reservationSearch'));
    document.getElementById('paymentSearch')?.addEventListener('input', () => filterTable('paymentTableBody', 'paymentSearch'));
    document.getElementById('notificationSearch')?.addEventListener('input', () => {
        const searchText = document.getElementById('notificationSearch').value.toLowerCase();
        const notifications = document.querySelectorAll('#notificationList li');
        
        notifications.forEach(notification => {
            const text = notification.textContent.toLowerCase();
            notification.style.display = text.includes(searchText) ? '' : 'none';
        });
    });
}

// Fetch and update customer table
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        const customers = await response.json();
        const tbody = document.getElementById('userTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        customers.forEach(customer => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${customer.id}</td>
                <td>${customer.username}</td>
                <td>${customer.email}</td>
                <td>
                    <span class="badge bg-${customer.active ? 'success' : 'danger'}">
                        ${customer.active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="editCustomer(${customer.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-${customer.active ? 'danger' : 'success'} btn-sm" 
                            onclick="${customer.active ? 'deactivateCustomer' : 'activateCustomer'}(${customer.id})">
                        ${customer.active ? 'Deactivate' : 'Activate'}
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading customers:', error);
        showToast('Error loading customers', 'danger');
    }
}

// Create new customer
async function createCustomer() {
    const username = prompt('Enter customer username:');
    if (!username) return;

    const email = prompt('Enter customer email:');
    if (!email) return;

    const password = prompt('Enter customer password:');
    if (!password) return;

    try {
        const response = await fetch('/api/customers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        if (response.ok) {
            showToast('Customer created successfully', 'success');
            loadCustomers();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to create customer', 'danger');
        }
    } catch (error) {
        console.error('Error creating customer:', error);
        showToast('Failed to create customer', 'danger');
    }
}

// Edit customer
async function editCustomer(customerId) {
    try {
        const response = await fetch(`/api/customers/${customerId}`);
        const customer = await response.json();

        const username = prompt('Enter new username:', customer.username);
        if (!username) return;

        const email = prompt('Enter new email:', customer.email);
        if (!email) return;

        const updatePassword = confirm('Do you want to update the password?');
        const password = updatePassword ? prompt('Enter new password:') : null;

        const updateData = {
            username,
            email
        };

        if (password) {
            updateData.password = password;
        }

        const updateResponse = await fetch(`/api/customers/${customerId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        if (updateResponse.ok) {
            showToast('Customer updated successfully', 'success');
            loadCustomers();
        } else {
            const data = await updateResponse.json();
            showToast(data.error || 'Failed to update customer', 'danger');
        }
    } catch (error) {
        console.error('Error updating customer:', error);
        showToast('Failed to update customer', 'danger');
    }
}

// Deactivate customer
async function deactivateCustomer(customerId) {
    if (!confirm('Are you sure you want to deactivate this customer?')) return;

    try {
        const response = await fetch(`/api/customers/${customerId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                active: false
            })
        });

        if (response.ok) {
            showToast('Customer deactivated successfully', 'success');
            loadCustomers();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to deactivate customer', 'danger');
        }
    } catch (error) {
        console.error('Error deactivating customer:', error);
        showToast('Failed to deactivate customer', 'danger');
    }
}

// Activate customer
async function activateCustomer(customerId) {
    try {
        const response = await fetch(`/api/customers/${customerId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                active: true
            })
        });

        if (response.ok) {
            showToast('Customer activated successfully', 'success');
            loadCustomers();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to activate customer', 'danger');
        }
    } catch (error) {
        console.error('Error activating customer:', error);
        showToast('Failed to activate customer', 'danger');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    const container = document.getElementById('toastContainer') || document.body;
    container.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Fetch and update locker table
async function loadLockers() {
    try {
        const response = await fetch('/api/lockers');
        const lockers = await response.json();
        const tbody = document.getElementById('lockerTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        lockers.forEach(locker => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${locker.number}</td>
                <td><span class="badge bg-${getStatusColor(locker.status)}">${locker.status}</span></td>
                <td>${locker.assigned_user_name || '-'}</td>
                <td>
                    ${locker.status === 'occupied' ? 
                        `<button class="btn btn-warning btn-sm">Release</button>` :
                        `<button class="btn btn-primary btn-sm">Assign</button>`}
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading lockers:', error);
    }
}

// Fetch and update reservation table
async function loadReservations() {
    try {
        const response = await fetch('/api/reservations');
        const reservations = await response.json();
        const tbody = document.getElementById('reservationTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        reservations.forEach(reservation => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${reservation.id}</td>
                <td>${reservation.user_id}</td>
                <td>${reservation.locker_id}</td>
                <td>${reservation.start_time}</td>
                <td><span class="badge bg-${getStatusColor(reservation.status)}">${reservation.status}</span></td>
                <td>
                    ${reservation.status === 'pending' ? 
                        `<button class="btn btn-danger btn-sm">Cancel</button>` : '-'}
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading reservations:', error);
    }
}

// Fetch and update payment table
async function loadPayments() {
    try {
        const response = await fetch('/api/payments');
        const payments = await response.json();
        const tbody = document.getElementById('paymentTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        payments.forEach(payment => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${payment.id}</td>
                <td>${payment.user_id}</td>
                <td>$${payment.amount.toFixed(2)}</td>
                <td>${payment.payment_date}</td>
                <td><span class="badge bg-${getStatusColor(payment.status)}">${payment.status}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading payments:', error);
    }
}

// Fetch and update notifications
async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const notifications = await response.json();
        const list = document.getElementById('notificationList');
        if (!list) return;
        
        list.innerHTML = '';
        notifications.forEach(notification => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${notification.title}</strong>
                        <p class="mb-0">${notification.message}</p>
                    </div>
                    <span class="badge bg-${getStatusColor(notification.type)}">${notification.type}</span>
                </div>
                <small class="text-muted">${notification.timestamp}</small>
            `;
            list.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

// Fetch and update dashboard statistics
async function updateDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Update the charts with real data
        // You can implement this based on your needs
    } catch (error) {
        console.error('Error fetching dashboard stats:', error);
    }
}

// Helper function to get status color
function getStatusColor(status) {
    switch (status?.toLowerCase()) {
        case 'occupied':
        case 'active':
        case 'completed':
        case 'success':
            return 'success';
        case 'available':
        case 'info':
            return 'primary';
        case 'pending':
        case 'warning':
            return 'warning';
        case 'cancelled':
        case 'error':
        case 'danger':
            return 'danger';
        default:
            return 'secondary';
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    initializeSearchListeners();
    loadCustomers();
    loadLockers();
    loadReservations();
    loadPayments();
    loadNotifications();
    
    // Update dashboard stats periodically
    updateDashboardStats();
    setInterval(updateDashboardStats, 30000); // Update every 30 seconds
}); 