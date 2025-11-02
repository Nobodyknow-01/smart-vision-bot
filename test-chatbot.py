from chatbot import router

tests = [
     "news from USA",
    "latest news in London",
    "technology news Japan",
    "economy news China",
    "weather news Canada"


# ==============================
# 💼 BUSINESS & FINANCE
# ==============================

    "stock market news today",
    "cryptocurrency latest updates",
    "bitcoin news",
    "finance and economy headlines",
    "Indian GDP news"

# ==============================
# ⚙️ TECHNOLOGY / SCIENCE
# ==============================

    "AI and machine learning news",
    "latest tech updates",
    "SpaceX news",
    "science discoveries this week",
    "smartphone launches 2025"


# ==============================
# ⚽ SPORTS / ENTERTAINMENT
# ==============================

    "cricket news India",
    "FIFA world cup updates",
    "Olympics 2025 news",
    "Hollywood latest movies",
    "music industry updates"

# ==============================
# 🧠 SPECIFIC TOPICS / PEOPLE
# ==============================

    "news about Elon Musk",
    "latest updates on Apple company",
    "Ukraine Russia conflict updates",
    "climate change news",
    "WHO covid updates"
    
    
]

for q in tests:
    print("\nQuery:", q)
    src, ans = router.route(q)
    print("Source:", src)
    print("Answer:", ans)
