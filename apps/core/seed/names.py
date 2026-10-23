"""Name lists for seed_demo. Plain lists instead of Faker, because Faker is a dev-only
dependency and staging runs seed_demo with the production install (uv sync --no-dev)."""

# fmt: off
FIRST_NAMES = [
    "Ahmet", "Ali", "Arda", "Ayşe", "Aylin", "Barış", "Berk", "Beyza", "Burak", "Büşra",
    "Can", "Cem", "Ceren", "Defne", "Deniz", "Derya", "Ece", "Efe", "Ege", "Elif",
    "Emir", "Emre", "Esra", "Gizem", "Gökhan", "Hakan", "Hande", "İrem", "Kaan", "Kerem",
    "Mehmet", "Melis", "Merve", "Mert", "Murat", "Nazlı", "Onur", "Özge", "Selin", "Serkan",
    "Seda", "Sinem", "Tolga", "Tuğba", "Umut", "Yağmur", "Yusuf", "Zehra", "Zeynep", "Fatma",
]

LAST_NAMES = [
    "Acar", "Akın", "Aksoy", "Aslan", "Avcı", "Aydın", "Balcı", "Bulut", "Çakır", "Çelik",
    "Demir", "Doğan", "Erdem", "Eren", "Güler", "Güneş", "Işık", "Kaplan", "Kara", "Kaya",
    "Keskin", "Koç", "Korkmaz", "Kurt", "Özdemir", "Özkan", "Öztürk", "Polat", "Sarı", "Şahin",
    "Şen", "Tekin", "Temiz", "Turan", "Uçar", "Ünal", "Uysal", "Yalçın", "Yavuz", "Yıldırım",
]
# fmt: on