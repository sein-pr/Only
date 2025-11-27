# Only

## Overview
Only is an e-commerce web application developed using the Flask framework. This project aims to provide a seamless shopping experience with integrated payment processing capabilities.

## Features
- **Product Catalog**: Browse and search through a wide range of products.
- **User Authentication**: Secure login and registration for users.
- **Shopping Cart**: Add products to a shopping cart for easy checkout.
- **Payment Gateway Integration**: Initially integrated with PayPal, now switched to Stripe for enhanced payment processing.
- **Order Management**: Users can view their order history and manage their purchases.
- **Responsive Design**: Built with HTML and CSS to ensure a smooth experience across devices.

## Technology Stack
- **Python**: The core programming language used for backend development.
- **Flask**: The web framework that powers the application.
- **HTML/CSS**: For frontend design and layout.

## Installation
To set up the project locally, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/sein-pr/Only.git
   ```

2. **Navigate to the Project Directory**
   ```bash
   cd Only
   ```

3. **Install Dependencies**
   Ensure you have Python and pip installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   
   Create a `.env` file in the project root directory by copying the example file:
   ```bash
   cp .env.example .env
   ```
   
   Then edit the `.env` file and add your configuration values:
   
   **Required Variables:**
   - `SECRET_KEY`: Flask secret key for session management
   - `BACK4APP_APP_ID`: Your Back4App Application ID
   - `BACK4APP_MASTER_KEY` or `BACK4APP_CLIENT_KEY`: Back4App authentication key
   
   **Optional Variables:**
   - Database configuration (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
   - Stripe keys for payment processing
   - Email configuration for password reset functionality
   
   **Important Notes:**
   - The `.env` file is loaded automatically when the application starts
   - Never commit your `.env` file to version control (it's in `.gitignore`)
   - For production deployment, use platform-provided environment variables instead of `.env` files
   - Environment variables from `.env` file take precedence over system environment variables

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Application**
   Open your browser and go to `http://127.0.0.1:5000/`.

## Contributing
Contributions are welcome! If you would like to contribute to the project, please fork the repository and submit a pull request.

## License
This project does not have a specified license. Please check the repository for any updates regarding licensing.

## Contact
For inquiries or feedback, please reach out via the GitHub repository.

---

Feel free to modify any sections to better fit the project's specifics or your preferences!
