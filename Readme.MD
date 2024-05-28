# Digital Ground
>This is a light-weight e-commerce application built on **Python Django**.

### In this project...:
* ***Twilio OTP Verification**: Secure user authentication via One-Time Password (OTP) using Twilio.*
* ***Razorpay Payment Gateway**: Seamless payment processing integrated with Razorpay.*
* ***Invoice Management**: Generate and download purchase invoices as PDFs.<small>(view and download)</small>*
* ***Location Services**: Retrieve exact location details using third-party APIs based on PIN code.*
* **Cart Functionality**:
  * *Uses AJAX for seamless user experience without page reloads.*
  * *Operates without user login.*
* ***Password Reset**:Reset passwords via email.*
* ***Product Filtering and Sorting**: AJAX-powered filtering, sorting, and pagination for products.*
* ***Wishlist**: AJAX-based wishlist management with [AlertifyJS](https://alertifyjs.com/) notifications.*
* ***Admin Panel**: Customizable admin interface using [AdminLTE](https://django-jazzmin.readthedocs.io/).*
* ***Database**: PostgreSQL for robust data management.*
<br>

## Live Demonstration

* ### Live Link  -> [View 📺](https://digitalground.pythonanywhere.com/)
* ### Screen Casting  -> [View 📺](https://www.linkedin.com/posts/sravankumarta_django-webdevelopment-djangodeveloper-activity-7020838489688596480-MPq7?utm_source=share&utm_medium=member_desktop)
<br>

## Getting Started

* Clone this repo :
  ```
  git clone https://github.com/sravan-kumar-ta/Digital_Ground--Django-.git
  cd Digital_Ground--Django-
  ```
* Create a virtual environment to install dependencies in and activate it:

  ```
  virtualenv venv
  source venv/bin/activate
  ``` 
* Then install the dependencies:
  ```
  pip install -r requirements.txt
  ```
* Run the project
  ```
  python manage.py makemigrations
  python manage.py migrate
  python manage.py runserver
  ```
* And navigate to `http://localhost:8000/`
<br>
<br>
<img align="center" alt="Coder GIF" width=150 src="https://raw.githubusercontent.com/gist/MedRedha/fd8e2481bde2610c96b9aafde543879c/raw/88624e8d31c4295973dcb7c900dacf0edc0a6d99/coding.gif" />

----------
[![Generic badge](https://img.shields.io/badge/Python-3.10.8-blue.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/Django-4.0.6-blue.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/Razorpay-1.3.0-blue.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/Twilio-7.16.0-blue.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/PyPDF3-1.0.3-blue.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/PyJWT-2.4.0-blue.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/django_jazzmin-2.6.0-blue.svg)](https://shields.io/)
