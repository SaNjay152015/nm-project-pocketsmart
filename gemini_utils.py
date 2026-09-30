import os
from dotenv import load_dotenv
from google import genai


load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


client = None

if API_KEY and API_KEY != "PASTE_YOUR_KEY_HERE":
    client = genai.Client(
        api_key=API_KEY
    )


PLATFORM_URLS = {
    "Amazon": "https://www.amazon.in/",
    "Flipkart": "https://www.flipkart.com/",
    "IKEA": "https://www.ikea.com/in/en/",
    "Swiggy": "https://www.swiggy.com/",
    "Zomato": "https://www.zomato.com/",
    "OYO": "https://www.oyorooms.com/"
}


def platform_links(platforms):
    links = []

    for platform in platforms:
        if platform in PLATFORM_URLS:
            links.append(
                f"{platform}: {PLATFORM_URLS[platform]}"
            )

    return "\n".join(links)


def clean_response(text):
    if not text:
        return ""

    return text.strip()


def ask_gemini(prompt, image_bytes=None, image_mime_type=None):
    if client is None:
        return None

    try:
        contents = []

        if image_bytes:
            contents.append(
                {
                    "inline_data": {
                        "mime_type": (
                            image_mime_type
                            or "image/jpeg"
                        ),
                        "data": image_bytes
                    }
                }
            )

        contents.append(prompt)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents
        )

        if response and response.text:
            return clean_response(
                response.text
            )

    except Exception as error:
        print(
            "Gemini error:",
            type(error).__name__,
            str(error)
        )

    return None


def home_fallback(
    budget,
    room,
    style,
    items,
    quantity
):
    return f"""
## 🏠 Home Interior Plan

**Room:** {room}  
**Style:** {style}  
**Budget:** ₹{budget:,.0f}  
**Requested quantity:** {quantity}  
**Items:** {items}

### Suggested Allocation

- Furniture & major items: 45%
- Lighting & electrical: 20%
- Decor: 20%
- Accessories: 10%
- Buffer: 5%

### Platforms to Compare

**IKEA** — furniture, lighting and storage

**Amazon** — electronics, lighting, decor and accessories

**Flipkart** — appliances and household products

### Important

These are planning estimates rather than live product prices.
Check the current price, delivery charge and availability before buying.
"""


def party_fallback(
    budget,
    guests,
    event_type,
    venue
):
    catering = budget * 0.45
    decoration = budget * 0.20
    venue_budget = budget * 0.20
    entertainment = budget * 0.10
    buffer = budget * 0.05

    return f"""
## 🎉 Party Budget Plan

**Event:** {event_type}  
**Guests:** {guests}  
**Venue:** {venue}  
**Total Budget:** ₹{budget:,.0f}

### Suggested Allocation

| Category | Suggested Amount |
|---|---:|
| Catering | ₹{catering:,.0f} |
| Decoration | ₹{decoration:,.0f} |
| Venue | ₹{venue_budget:,.0f} |
| Entertainment | ₹{entertainment:,.0f} |
| Emergency Buffer | ₹{buffer:,.0f} |

### Platforms to Compare

- **Swiggy** — food and catering options
- **Zomato** — restaurants and food services
- **OYO** — accommodation/venue-related options

Prices and availability must be checked on the respective platforms.
"""


def jewelry_fallback(
    budget,
    occasion,
    style
):
    return f"""
## 💎 Jewelry Recommendation

**Budget:** ₹{budget:,.0f}  
**Occasion:** {occasion}  
**Style:** {style}

### Suggested Options

1. **Minimal earrings**
   - Suitable for a clean and elegant look
   - Suggested budget: ₹{budget * 0.25:,.0f}

2. **Statement necklace**
   - Useful for festive or formal outfits
   - Suggested budget: ₹{budget * 0.40:,.0f}

3. **Bracelet / bangle**
   - Can complement the main jewelry
   - Suggested budget: ₹{budget * 0.20:,.0f}

4. **Reserve**
   - Keep approximately 15% for adjustments or accessories

### Platforms to Compare

- Amazon
- Flipkart

Always verify current price, material, seller information and return policy.
"""


def get_budget_recommendation(
    income,
    food,
    transport,
    shopping,
    bills
):
    spent = (
        food
        + transport
        + shopping
        + bills
    )

    remaining = income - spent

    prompt = f"""
You are PocketSmart AI, a practical personal budgeting assistant.

User monthly income:
₹{income:,.2f}

Current expenses:
Food: ₹{food:,.2f}
Transport: ₹{transport:,.2f}
Shopping: ₹{shopping:,.2f}
Bills: ₹{bills:,.2f}

Total spent:
₹{spent:,.2f}

Remaining:
₹{remaining:,.2f}

Create a practical budget analysis.

Include:

1. Spending summary
2. Category percentages
3. Areas where spending can be reduced
4. Suggested allocation for remaining money
5. A realistic savings target
6. Three simple actions for the next month

Do not provide investment, tax, loan or regulated financial advice.

Keep the answer clear and beginner-friendly.
"""

    result = ask_gemini(prompt)

    if result:
        return result

    return f"""
## 💰 Budget Summary

**Income:** ₹{income:,.0f}

**Current spending:** ₹{spent:,.0f}

**Remaining:** ₹{remaining:,.0f}

Your current spending is approximately
{(spent / income * 100) if income else 0:.1f}% of your income.

Review the highest spending categories first and keep a small emergency buffer.
"""


def get_home_recommendation(
    budget,
    room,
    style,
    items,
    quantity
):
    prompt = f"""
You are PocketSmart AI's Home Interior Planner.

Budget:
₹{budget:,.2f}

Room:
{room}

Preferred style:
{style}

Requested items:
{items}

Quantity:
{quantity}

Create a realistic budget-conscious home setup.

IMPORTANT:
Use these platforms as recommendation sources:
- IKEA
- Amazon
- Flipkart

Do NOT claim that you accessed live product databases.

For every suggested item provide:

- Item
- Suggested quantity
- Approximate budget range
- Suitable platform
- Why it fits
- Search keywords

Include:
1. Budget allocation
2. Product/item recommendations
3. Platform comparison
4. Estimated total
5. Remaining buffer

Clearly state that prices are estimates and must be verified.

Do not recommend spending above the supplied budget.
"""

    result = ask_gemini(prompt)

    if result:
        return result

    return home_fallback(
        budget,
        room,
        style,
        items,
        quantity
    )


def get_party_recommendation(
    budget,
    guests,
    event_type,
    venue
):
    prompt = f"""
You are PocketSmart AI's Party Planner.

Total budget:
₹{budget:,.2f}

Guest count:
{guests}

Event:
{event_type}

Venue:
{venue}

Create a practical event plan.

Use these platforms as recommendation sources:

- Swiggy
- Zomato
- OYO

Do NOT pretend that you have live vendor availability.

Allocate the budget between:

- Catering
- Venue
- Decoration
- Entertainment
- Miscellaneous/buffer

For each recommendation include:

- Category
- Suggested amount
- Suitable platform
- Search keywords
- Reason

Calculate the total and ensure it does not exceed the budget.

Prices and availability must be verified by the user.
"""

    result = ask_gemini(prompt)

    if result:
        return result

    return party_fallback(
        budget,
        guests,
        event_type,
        venue
    )


def get_jewelry_recommendation(
    budget,
    occasion,
    style,
    image_bytes=None,
    image_mime_type="image/jpeg"
):
    prompt = f"""
You are PocketSmart AI's Jewelry Planner.

Budget:
₹{budget:,.2f}

Occasion:
{occasion}

Preferred style:
{style}

The user may have uploaded an outfit image.

If an image is provided:

Analyze only visible fashion information such as:
- dominant colors
- patterns
- neckline
- visible accessories
- general visual style

Do NOT identify the person.

Recommend jewelry that coordinates with the outfit.

Use:
- Amazon
- Flipkart

Do NOT claim live product availability.

For each suggestion include:

1. Jewelry type
2. Suggested material/style
3. Approximate budget range
4. Suitable platform
5. Search keywords
6. Why it matches

Stay within the user's budget.

Mention that prices and availability must be verified.
"""

    result = ask_gemini(
        prompt,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type
    )

    if result:
        return result

    return jewelry_fallback(
        budget,
        occasion,
        style
    )


def get_jarvis_response(
    question,
    session_data=None
):
    context = session_data or {}

    prompt = f"""
You are JARVIS, the conversational assistant inside PocketSmart AI.

User question:
{question}

Known user/session context:
{context}

Help the user with:
- budgeting
- planning
- PocketSmart features
- home planning
- party planning
- jewelry planning
- expense organization

Be concise and practical.

Do not provide investment, tax, loan or regulated financial advice.
"""

    result = ask_gemini(prompt)

    if result:
        return result

    return (
        "I can help you plan budgets, "
        "home interiors, parties, jewelry, "
        "expenses and recommendations."
    )