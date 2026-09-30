PocketSmart AI: Your Smart Budget & Recommendation Assistant
Managing budgets across different life needs—such as home decor, event planning, or jewelry shopping—can be overwhelming due to the vast variety of products, platforms, and price ranges. PocketSmart AI addresses this challenge through a Generative AI–powered, cross-platform recommendation system that delivers personalized, budget-conscious suggestions for products and services.   
PDF
+ 1

Powered by Gemini 1.5 Flash Pro and a FastAPI / Flask backend framework, PocketSmart AI analyzes user preferences, overall budgets, and contextual requirements. It generates curated recommendations with shopping links across leading platforms like Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, MakeMyTrip, and BookMyShow.   
PDF
+ 4

Key Features & Use Cases
1. Home Interior Budget Planner
Smart Allocation: Users specify room types (Living Room, Kitchen, Bedroom) and fixture/furniture quantities (lights, ceiling fans, dining tables) along with a total budget.   
PDF
+ 1

Cross-Platform Suggestions: Generates cost-effective, styled items balanced across functionality and budget.   
PDF

Direct Market Links: Provides direct search links for Indian e-commerce sites (Amazon India, Flipkart, IKEA, Myntra, Ajio).   
PDF

2. AI-Based Party Budget Planner
Proportional Splitting: Allocates budgets dynamically across venue booking, catering, decorations, and entertainment based on total budget, guest count, and event type (wedding, birthday, corporate).   
PDF
+ 1

Service Sourcing: Connects user preferences with local and online service platforms such as Swiggy, Zomato, BookMyShow, BigBasket, and OYO.   
PDF
+ 1

Contingency & Suggestions: Automatically factors in cost breakdown calculations and fallback recommendations.   
PDF
+ 1

3. Jewelry & Outfit Recommendation Planner
Multimodal Analysis: Users can upload an outfit image to let the AI analyze color coordination, design, and formality levels.   
PDF
+ 1

Occasion-Based Matching: Recommends jewelry options aligned with specific occasions (e.g., weddings, birthdays, casual events).   
PDF
+ 1

Platform Integration: Directly links to specialized retailers like Tanishq, CaratLane, BlueStone, Melorra, Meesho, and Amazon.   
PDF

4. User Dashboard & Plan History
Authentication: Secure user signup, login, and token-based session management using JWT.   
PDF
+ 1

Plan History: Allows users to log, review, and reuse their past budget plans and recommendation sets.   
PDF
+ 2

Tech Stack
Backend Framework: FastAPI / Flask (Python)   
PDF
+ 1

Generative AI Model: Google Gemini 1.5 Flash Pro (Multimodal)   
PDF
+ 1

Frontend: HTML5, CSS3, JavaScript, Jinja2 Templates   
PDF
+ 2

Authentication: OAuth2 with Password Hashing (Bcrypt) & JWT (JOSE)   
PDF
+ 1

Image Processing: PIL (Pillow)   
PDF
+ 1

Environment Configuration: python-dotenv

   
PDF
+ 1

Repository Structure
Plaintext
PocketSmart-AI/
├── static/
│   ├── uploads/            # Uploaded outfit images for analysis
│   └── styles.css          # Core CSS stylesheet
├── templates/
│   ├── index.html          # Main landing page
│   ├── login.html          # User login page
│   ├── register.html       # User registration page
│   ├── dashboard.html      # Central user hub
│   ├── home_planner.html   # Home interior budget planner interface
│   ├── party_planner.html  # Party planning interface
│   ├── jewelry_planner.html# Multimodal jewelry planner interface
│   └── history.html        # Recommendation history log page
├── .env                    # Environment variables (API Keys, Secret Key)
├── main.py / app.py        # Core FastAPI application server & routes
└── README.md               # Project documentation
Prerequisites
Before running the project, ensure you have:

Python 3.9+ installed.

A valid Google Gemini API Key obtained from Google AI Studio.   
PDF
+ 2

Installation & Setup Instructions
1. Clone the Repository
Bash
git clone https://github.com/your-username/PocketSmart-AI.git
cd PocketSmart-AI
2. Create and Activate a Virtual Environment
Bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
Bash
pip install fastapi uvicorn google-generativeai python-dotenv passlib[bcrypt] python-jose python-multipart pillow
4. Configure Environment Variables
Create a .env file in the root directory and define the following variables:   
PDF
+ 1

Code snippet
GOOGLE_API_KEY=your_google_gemini_api_key_here
SECRET_KEY=your_jwt_secret_key_here
5. Run the Application
Start the server using Uvicorn:   
PDF

Bash
python -m uvicorn main:app --reload
Alternatively, execute:

Bash
py -m uvicorn main:app --reload
   
PDF
Access the application in your browser at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

   
PDF

API Routes Overview
Method	Endpoint	Description
GET	/	
Renders the main landing page 
PDF
+ 1

POST	/token	
Authenticates user and returns JWT access token 
PDF

POST	/home-budget	
Generates home interior budget recommendations 
PDF

POST	/party-budget	
Generates party budget allocations and vendor suggestions 
PDF

POST	/jewelry-budget	
Accepts text/image inputs for jewelry recommendations 
PDF

GET	/recommendation-history	
Fetches historical recommendation plans for the active user 
PDF
+ 1

Made by Sanjay S
