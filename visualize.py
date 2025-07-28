from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('subscribers_cleaned.csv')
all_interests = ' '.join(df['interests'].dropna())

wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_interests)

plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.savefig('graphs/interests_wordcloud.png')
plt.show()
