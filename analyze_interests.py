import pandas as pd
from collections import Counter
import re
import matplotlib.pyplot as plt
import os

os.makedirs('graphs', exist_ok=True)

df = pd.read_csv('subscribers_cleaned.csv')
all_interests = ' '.join(df['interests'].dropna())

def extract_words(text):
    words = re.findall(r'\b[а-яa-zё]{3,}\b', text.lower())
    return words

words = extract_words(all_interests)
word_counts = Counter(words)
top_30_interests = word_counts.most_common(30)

print("\nТОП-30 интересов:")
for word, count in top_30_interests:
    print(f"{word}: {count}")

pd.DataFrame(top_30_interests, columns=['Interest', 'Count']).to_csv('top_30_interests.csv', index=False)

labels, values = zip(*top_30_interests)
plt.figure(figsize=(12, 8))
plt.barh(labels[::-1], values[::-1])
plt.title('ТОП-30 интересов подписчиков')
plt.xlabel('Частота')
plt.ylabel('Интересы')
plt.tight_layout()
plt.savefig('graphs/top_30_interests.png')
