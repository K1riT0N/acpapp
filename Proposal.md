# Mini Project: Advanced Computer Programming

**By Aj. Sarucha Yanyong**

**Project Name:** SME Booking System

**Team Members:**
- Napat Srivitidkul — 68011391
- Nathi Ritnatikul — 68011399
- Phawinee Sangkhamanee — 68011462
- Fineena Karon Brown — 68011330

---

## Project Overview

In the world of business, the issues that still exist in SME businesses are lack of an automated system, limited budget (cause low brand awareness) and low customer satisfaction due to slow response time and weak follow ups that can cause inconsistency in services. Therefore, we decided to do an application specifically for SME business to help them gain more visibility from customers via the website and help to manage their daily issues by having these operations:

The customer can book a scheduled appointment they need through the website and there will be a message alerting the shop that there's a queue coming. After that the system will track the date and send a message to remind customers and businesses for the appointment. This can raise the shop management efficiency by not forgetting the customer queue that came from the phone confirmation or other platforms and know how many customers they can handle according to the amount that came in each day.

Additionally, to protect SMEs from losses caused by cancellations or no-shows, the website requires customers to pay a deposit, which will be a certain percentage of the service price. Then, at the time of the appointment, customers have to pay the rest. However, if the customer cancels, the deposit is non-refundable.

Lastly, the website will also contain a function of user status like Ordinary (Free) where the booking privilege will be limited to a certain number of customers per month. In case the shop wants the number of bookings to be unlimited, they can choose to pay for a monthly subscription to upgrade themselves into Pro status.

---

## Functional Requirements

The features and actions a user can perform, from registering an account to completing a booking. The features are listed below and they define the minimum feature set needed for the platform to function as a usable booking and subscription service for both businesses and their customers.

- A business can register and log in
- A business can create, edit, and delete services
- A customer can view a business's public booking page and select a service and time slot without creating an account
- A customer can complete a simulated deposit payment to confirm a booking
- A business can view, confirm, cancel, and mark bookings as completed
- A business can upgrade from Free to Pro subscription, billed monthly or annually
- The system enforces tier limits (Free and Pro)
- An Admin can view platform-wide KPIs across all businesses

## Non-functional Requirements

The quality standards, constraints, and characteristics that apply across the whole platform rather than to any single feature. These features ensure that the website is secure, trustworthy and easy to use.

- Passwords hashed (JWT-based authentication and session handling)
- The system UI/UX must be usable for both desktop and mobile
- Booking confirmation should happen within a couple seconds of payment
- System must show clear error messages when something's invalid

---

## Monetization & Feature Gating

**Business Model:** Our website offers a Free tier for SMEs to get started at no cost, and a Pro tier that unlocks additional features for businesses that want a more complete solution.

**Tier Comparison**

| Feature | Free | Pro |
|---|---|---|
| Active services | Limited | Unlimited |
| Bookings per month | Limited | Unlimited |
| Email/SMS notifications | No | Yes |
| Deposit collection | Yes | Yes |
| Booking Analytics | Basic | Advanced |

**Payment / Checkout Flow:**
- The system will have an Upgrade button for business/SME to change from Free to Pro tier which will have a simulated payment screen and will update the user subscription tier and unlock more features
- On success, the user subscription will be updated with the new tier and also added the expiry date for that subscription
- The Upgrade flow lets the business choose monthly or annual billing before proceeding to the simulated payment screen

**Deposit Flow (Per Booking):**
When the customer is booking for services, they are required to pay for the deposit equal to a percentage of that service's price, such as 10–20%, which can be set by the business. The remaining balance is paid directly to the business at the time of the appointment. If the customer cancels the booking, the deposit is not refundable. This helps ensure that our website is trustworthy.

**Enforcement:**
- Each business account will have a subscription tier and expiration date in the users table
- We use FastAPI to check server-side that reads the requesting business's current tier before the action is allowed
- For each request, the system compares the expiration date against the current date. If expired and not renewed, the tier is automatically reverted to Free until the business upgrades again

---

## Timeline

| Week | Phase | Deliverable |
|---|---|---|
| 1 | Requirements Gathering | Confirm scope, tiers, and page list. Finalized the Proposal |
| 2 | Design + Core CRUD | Wireframes, user flow diagram (~40% complete) |
| 3 | Feature Development | Deposit checkout, subscription tiers, notifications (~70% complete) |
| 4 | Dashboard + Testing | Admin analytics dashboard built (Progress Demo Video) |
| 5 | Finalize + Deploy | Final Design Document, full website demo video and Product deployment |

**Milestones**
- Completion of database design
- Completion of authentication functionality
- Completion of the booking CRUD workflow
- Completion of the Free/Pro paywall and checkout
- Completion of the admin analytics dashboard
- Production deployment

---

## Conclusion

This proposal shows a booking and queue management platform built specifically for SMEs. This addresses common pain points about low visibility, inconsistent follow-ups, and profit lost to no-shows through a solution model built around a percentage-based, non-refundable booking deposit. The platform offers businesses a practical tool to manage daily booking more reliably. Development will proceed across five weeks, moving from core booking and authentication features toward the subscription, admin analytics dashboard and full deployment.
