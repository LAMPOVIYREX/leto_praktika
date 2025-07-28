import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
os.makedirs('graphs', exist_ok=True)

class AudienceAnalyzer:
    def __init__(self):
        self.df = self.load_and_clean_data()
    
    def load_and_clean_data(self):
        df = pd.read_csv('subscribers.csv')
        df = df[df['first_name'] != 'DELETED']
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        df = df[(df['age'] >= 14) & (df['age'] <= 80)]
        gender_map = {1: 'Женский', 2: 'Мужской'}
        df['gender'] = df['sex'].map(gender_map)
        df.to_csv('subscribers_cleaned.csv', index=False)
        return df
    
    def plot_demographics(self):
        plt.figure(figsize=(8, 5))
        self.df['gender'].value_counts().plot(kind='pie', autopct='%1.1f%%')
        plt.title('Распределение по полу')
        plt.savefig('graphs/gender_distribution.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df['age'], bins=20, kde=True)
        plt.title('Распределение по возрасту')
        plt.xlabel('Возраст')
        plt.ylabel('Количество подписчиков')
        plt.savefig('graphs/age_distribution.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        self.df['city'].value_counts().head(10).plot(kind='barh')
        plt.title('Топ-10 городов')
        plt.xlabel('Количество подписчиков')
        plt.tight_layout()
        plt.savefig('graphs/city_distribution.png')
        plt.close()
    
    def compare_with_competitors(self):
        competitors = []
        for file in os.listdir('competitors_data'):
            if file.endswith('_subscribers.csv'):
                df = pd.read_csv(f'competitors_data/{file}')
                competitors.append({
                    'name': file.replace('_audience.csv', ''),
                    'data': df
                })
        
        if not competitors:
            print("Нет данных конкурентов для сравнения")
            return
        
        plt.figure(figsize=(12, 6))
        sns.kdeplot(self.df['age'], label='Laser33', linewidth=3)
        for comp in competitors:
            sns.kdeplot(comp['data']['age'], label=comp['name'])
        plt.title('Сравнение возрастного распределения')
        plt.xlabel('Возраст')
        plt.legend()
        plt.savefig('graphs/age_comparison.png')
        plt.close()
        
        top_cities = self.df['city'].value_counts().head(5).index
        city_data = []
        for city in top_cities:
            row = {'city': city, 'Laser33': sum(self.df['city'] == city)}
            for comp in competitors:
                row[comp['name']] = sum(comp['data']['city'] == city)
            city_data.append(row)
        
        df_cities = pd.DataFrame(city_data).set_index('city')
        df_cities.plot(kind='bar', figsize=(12, 6))
        plt.title('Сравнение по городам')
        plt.ylabel('Количество подписчиков')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('graphs/city_comparison.png')
        plt.close()
    
    def analyze_engagement(self):
        if not os.path.exists('results/posts_stats.csv'):
            print("Нет данных по постам")
            return
        
        posts = pd.read_csv('results/posts_stats.csv')
        posts['engagement'] = posts['likes'] + posts['reposts']*2
        
        merged = pd.merge(
            self.df[['id', 'age']], 
            posts, 
            left_on='id', 
            right_on='post_id', 
            how='inner'
        )
        
        plt.figure(figsize=(10, 6))
        sns.regplot(x='age', y='engagement', data=merged)
        plt.title('Зависимость вовлеченности от возраста')
        plt.savefig('graphs/age_engagement.png')
        plt.close()
    
    def run_full_analysis(self):
        print("Анализ демографии...")
        self.plot_demographics()
        print("\nСравнение с конкурентами...")
        self.compare_with_competitors()
        print("\nАнализ вовлеченности...")
        self.analyze_engagement()
        print("\nВсе графики сохранены в папке graphs")

if __name__ == "__main__":
    analyzer = AudienceAnalyzer()
    analyzer.run_full_analysis()
