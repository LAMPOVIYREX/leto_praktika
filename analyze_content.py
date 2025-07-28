import vk_api
from datetime import datetime
import pandas as pd
import re
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

TOKEN = 'ТОКЕН'
VERSION = '5.131'
GROUP_ID = -165542199
os.makedirs('results', exist_ok=True)
os.makedirs('graphs/content', exist_ok=True)

class ContentAnalyzer:
    def __init__(self):
        self.posts = self.get_all_posts()
    
    def get_all_posts(self, count=100):
        try:
            vk_session = vk_api.VkApi(token=TOKEN)
            vk = vk_session.get_api()
            posts = vk.wall.get(
                owner_id=GROUP_ID,
                count=count,
                extended=1,
                fields='attachments',
                v=VERSION
            )
            return posts.get('items', [])
        except Exception as e:
            print(f"Ошибка API: {e}")
            return []

    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'\n+', ' ', str(text))
        return re.sub(r'\s+', ' ', text).strip()
    
    def parse_attachments(self, post):
        media = defaultdict(int)
        types = []
        for attach in post.get('attachments', []):
            media[attach['type']] += 1
            types.append(attach['type'])
        return {
            'media_types': ', '.join(types),
            'photos': media.get('photo', 0),
            'videos': media.get('video', 0),
            'docs': media.get('doc', 0)
        }

    def classify_content(self, text):
        text = str(text).lower()
        if re.search(r'кейс|пример|реализац', text):
            return 'Кейсы'
        elif re.search(r'акци|скидк|распродаж', text):
            return 'Акции'
        elif re.search(r'новост|событ|мероприят', text):
            return 'Новости'
        elif re.search(r'обучен|курс|технолог', text):
            return 'Обучение'
        return 'Другое'

    def analyze_posts(self):
        processed = []
        for post in self.posts:
            try:
                clean_txt = self.clean_text(post.get('text', ''))
                date = datetime.fromtimestamp(post['date'])
                
                stats = {
                    'likes': post.get('likes', {}).get('count', 0),
                    'reposts': post.get('reposts', {}).get('count', 0),
                    'comments': post.get('comments', {}).get('count', 0),
                    'views': post.get('views', {}).get('count', 0)
                }
                
                attachments = self.parse_attachments(post)
                content_type = self.classify_content(clean_txt)
                
                processed.append({
                    'post_id': post['id'],
                    'date': date,
                    'text': clean_txt,
                    'text_length': len(clean_txt),
                    'hashtags': len(re.findall(r'#\w+', clean_txt)),
                    'content_type': content_type,
                    **stats,
                    **attachments
                })
            except Exception as e:
                print(f"Ошибка обработки поста: {e}")
        
        return pd.DataFrame(processed)

    def visualize_content(self, df):
        plt.figure(figsize=(10, 6))
        df['content_type'].value_counts().plot(
            kind='pie',
            autopct='%1.1f%%',
            startangle=90,
            colors=['#4c72b0', '#55a868', '#c44e52', '#8172b2', '#ccb974']
        )
        plt.title('Распределение типов контента', pad=20)
        plt.ylabel('')
        plt.savefig('graphs/content/content_types.png', bbox_inches='tight')
        plt.close()
        
        engagement = df.groupby('content_type').agg({
            'likes': 'mean',
            'reposts': 'mean',
            'comments': 'mean'
        }).reset_index()
        
        engagement = engagement.sort_values('likes', ascending=False)
        
        bar_width = 0.25
        index = range(len(engagement))
        
        plt.figure(figsize=(10, 6))
        plt.bar(index, engagement['likes'], bar_width, label='Лайки', color='#4c72b0')
        plt.bar([i + bar_width for i in index], engagement['reposts'], bar_width, 
                label='Репосты', color='#55a868')
        plt.bar([i + 2*bar_width for i in index], engagement['comments'], bar_width,
                label='Комментарии', color='#c44e52')
        
        plt.xlabel('Тип контента')
        plt.ylabel('Среднее количество')
        plt.title('Вовлеченность по типам контента', pad=20)
        plt.xticks([i + bar_width for i in index], engagement['content_type'])
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('graphs/content/likes_by_type.png', dpi=300)
        plt.close()
        
        df['week'] = df['date'].dt.strftime('%Y-%U')
        weekly = df.groupby('week').size()
        plt.figure(figsize=(12, 6))
        weekly.plot(kind='bar', color='#4c72b0')
        plt.title('Количество постов по неделям')
        plt.xlabel('Неделя')
        plt.ylabel('Количество постов')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.savefig('graphs/content/posts_per_week.png', bbox_inches='tight')
        plt.close()
    
    def compare_with_competitors(self):
        competitors = []
        for file in os.listdir('competitors_data'):
            if file.endswith('_content.csv'):
                df = pd.read_csv(f'competitors_data/{file}')
                if 'text' in df.columns:
                    df['content_type'] = df['text'].apply(self.classify_content)
                    competitors.append({
                        'name': file.replace('_content.csv', ''),
                        'data': df
                    })
        
        if not competitors:
            print("Нет данных конкурентов для сравнения")
            return
        
        content_compare = []
        for comp in competitors:
            counts = comp['data']['content_type'].value_counts(normalize=True)*100
            content_compare.append({
                'name': comp['name'],
                'Кейсы': counts.get('Кейсы', 0),
                'Обучение': counts.get('Обучение', 0),
                'Акции': counts.get('Акции', 0),
                'Новости': counts.get('Новости', 0),
                'Другое': counts.get('Другое', 0)
            })
        
        df_compare = pd.DataFrame(content_compare).set_index('name')
        df_compare.plot(kind='bar', stacked=True, figsize=(12, 6), 
                       color=['#4c72b0', '#55a868', '#c44e52', '#8172b2', '#ccb974'])
        plt.title('Сравнение типов контента с конкурентами (%)')
        plt.ylabel('Процент от общего числа постов')
        plt.xticks(rotation=45)
        plt.legend(title='Тип контента')
        plt.tight_layout()
        plt.savefig('graphs/content/content_comparison.png', dpi=300)
        plt.close()
    
    def run_analysis(self):
        print("Анализ контента...")
        df = self.analyze_posts()
        df.to_csv('results/posts_stats.csv', index=False, encoding='utf-8-sig')
        print(f"Сохранено {len(df)} постов в results/posts_stats.csv")
        self.visualize_content(df)
        self.compare_with_competitors()
        print("Графики сохранены в graphs/content/")

if __name__ == "__main__":
    analyzer = ContentAnalyzer()
    analyzer.run_analysis()
