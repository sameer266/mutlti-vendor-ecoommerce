# Chance Store – How It Works

Chance Store is a **Django-based admin backend system** that manages **online sales, offline (physical) sales, and service bookings** in one place.  
All business operations are handled through the admin panel with automatic calculations and status updates.

---

## 1. User & Access Flow
- Users are created using Django’s user system.
- When an admin (superuser) is created:
  - An **Admin role** is automatically assigned.
  - A **User Profile** is created.
- Regular users act as **customers**.
- OTP verification can be used for additional user validation.

---

## 2. Product & Inventory Flow
- Admin creates **categories** and **products**.
- Each product stores:
  - Price and cost price
  - Stock quantity
  - Variants (size, color, RAM, etc.)
  - Shipping cost per product
  - Estimated delivery time
- Stock levels are updated automatically.
- Product data is preserved in orders so past records never change.

---

## 3. Cart & Checkout Flow
- Customers add products to the cart.
- Cart supports:
  - Logged-in users
  - Guest users (session-based)
- During checkout:
  - An order is created
  - Product price, shipping cost, and delivery estimates are saved as snapshots
  - Tax and discounts are applied
- Order totals are recalculated automatically.

---

## 4. Order & Payment Flow
- Orders support multiple payment methods.
- Payment status controls order status:
  - When payment becomes **Paid**, the order is automatically marked **Delivered**.
- Order status and payment status stay in sync.

---

## 5. Invoice Flow
- A customer invoice is generated for each order.
- Invoices store:
  - Order totals
  - Tax
  - Discount
  - Payment status
- Invoice payment status automatically follows the order payment status.

---

## 6. Coupon & Discount Flow
- Admin creates coupons with:
  - Valid dates
  - Usage limits
  - Minimum purchase rules
- Coupons are validated at checkout.
- Discount amount is calculated automatically and applied to the order.

---

## 7. Supplier & Purchase Flow
- Admin manages suppliers.
- Purchases are recorded from suppliers.
- Each purchase:
  - Stores product snapshots
  - Automatically calculates totals
- A purchase invoice is generated automatically to preserve historical data.

---

## 8. Offline (Physical) Sales Flow
- Admin creates offline customers.
- Sales are entered manually with:
  - Products
  - Total amount
  - Paid amount
- System automatically calculates:
  - Outstanding balance
  - Payment status (Paid / Partially Paid / Unpaid)
- Multiple payments can be recorded for one sale.

---

## 9. Services Booking Flow
- Admin creates service types (Electrician, Plumber, etc.).
- Customers are assigned to service bookings.
- Each booking tracks:
  - Selected service
  - Booking date
  - Status (Pending / Completed)

---

## 10. Notifications Flow
- Notifications are generated for:
  - Order updates
  - Product updates
  - Messages
- Users can view and mark notifications as read.

---

## 11. Global Rules & Automation
- A single global tax percentage is applied to all orders.
- Shipping cost is calculated per product.
- Django signals ensure:
  - Automatic total calculations
  - Invoice synchronization
  - Data consistency across orders, sales, and purchases

---

## Overall Workflow
Chance Store works as a **central control system** where:
- Online orders
- Offline sales
- Service bookings  

are managed together with **automatic calculations, invoices, and status handling**, ensuring accurate and reliable business records.
