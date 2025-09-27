paypal.Buttons({
    createOrder: function(data, actions) {
        // Call your /api/orders route to create the order
        return fetch('/api/orders', {
            method: 'post',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cart: cartData // Replace cartData with your actual cart data
            })
        }).then(function(response) {
            return response.json();
        }).then(function(order) {
            return order.id; // Return the order ID
        });
    },
    onApprove: function(data, actions) {
        // Call your /api/orders/<order_id>/capture route to capture the order
        return fetch(`/api/orders/${data.orderID}/capture`, {
            method: 'post'
        }).then(function(response) {
            return response.json();
        }).then(function(orderData) {
            // Handle successful payment (e.g., redirect to order confirmation)
            console.log('Capture result', orderData, JSON.stringify(orderData, null, 2));
            window.location.href = '/order-confirmation'; // Replace with your route
        });
    }
}).render('#paypal-button-container');
