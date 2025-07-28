import pandas as pd
from collections import Counter
import re
import json
import matplotlib.pyplot as plt
import os

def load_data():
    data = {
        'subscribers': pd.read_csv('subscribers_cleaned.csv'),
        'posts': pd.read_csv('results/posts_stats.csv'),
        'competitors': []
    }
    
    competitors_dir = 'competitors_clean'
    if os.path.exists(competitors_dir):
        for file in os.listdir(competitors_dir):
            if file.endswith('_clean.csv'):
                name = file.replace('_clean.csv', '')
                try:
                    df = pd.read_csv(f'{competitors_dir}/{file}')
                    stats_file = f'{competitors_dir}/{name}_meta.json'
                    stats = {}
                    if os.path.exists(stats_file):
                        with open(stats_file, 'r') as f:
                            stats = json.load(f)
                    
                    content_file = f'competitors_data/{name}_content.csv'
                    content = None
                    if os.path.exists(content_file):
                        content = pd.read_csv(content_file)
                    
                    data['competitors'].append({
                        'name': name,
                        'data': df,
                        'stats': stats,
                        'content': content
                    })
                except Exception as e:
                    print(f"Ошибка загрузки данных {name}: {e}")
    else:
        print(f"Папка {competitors_dir} не найдена")
    
    return data

def analyze_interests(df):
    all_interests = ' '.join(df['interests'].dropna().astype(str))
    words = re.findall(r'\b[а-яa-zё]{3,}\b', all_interests.lower())
    return Counter(words)

def generate_content_strategy(data):
    strategy = {
        'content_types': [],
        'posting_schedule': {},
        'collaborations': [],
        'kpi': {}
    }
    
    our_posts = data['posts']
    our_engagement = our_posts['likes'].mean() + our_posts['reposts'].mean()*2
    
    content_types = {
        'case_study': len(our_posts[our_posts['text'].str.contains('кейс|пример', case=False, na=False)]),
        'educational': len(our_posts[our_posts['text'].str.contains('обучен|технолог', case=False, na=False)]),
        'promo': len(our_posts[our_posts['text'].str.contains('акци|скидк', case=False, na=False)])
    }
    
    for comp in data['competitors']:
        if comp.get('content') is not None:
            try:
                comp_engagement = comp['content']['likes'].mean() + comp['content']['reposts'].mean()*2
                if comp_engagement > our_engagement:
                    comp_content = comp['content']
                    comp_case = len(comp_content[comp_content['text'].str.contains('кейс|пример', case=False, na=False)])
                    comp_edu = len(comp_content[comp_content['text'].str.contains('обучен|технолог', case=False, na=False)])
                    
                    if comp_case > content_types['case_study']:
                        strategy['content_types'].append(f"Увеличить долю кейсов (как у {comp['name']})")
                    if comp_edu > content_types['educational']:
                        strategy['content_types'].append(f"Добавить обучающих материалов (как у {comp['name']})")
            except:
                continue
    
    if 'date' in our_posts.columns:
        try:
            our_posts['hour'] = pd.to_datetime(our_posts['date']).dt.hour
            best_hours = our_posts.groupby('hour')['likes'].mean().nlargest(3).index.tolist()
            strategy['posting_schedule']['best_hours'] = best_hours
        except:
            strategy['posting_schedule']['best_hours'] = [12, 18, 20]
    
    strategy['posting_schedule']['best_days'] = ['Вт', 'Чт', 'Сб']
    
    if data['competitors']:
        top_competitors = sorted(
            [c for c in data['competitors'] if 'stats' in c and 'total_users' in c['stats']],
            key=lambda x: x['stats']['total_users'],
            reverse=True
        )[:2]
        strategy['collaborations'] = [
            f"Кросс-посты с {comp['name']}" for comp in top_competitors
        ]
    
    strategy['kpi'] = {
        'target_er': round(our_engagement * 1.3, 1),
        'new_subscribers': 150,
        'timeframe': '3 месяца'
    }
    
    return strategy

def visualize_strategy(strategy):
    plt.figure(figsize=(10, 4))
    pd.Series({
        'Кейсы': 35,
        'Обучение': 25,
        'Акции': 20,
        'Новости': 15,
        'Развлечение': 5
    }).plot(kind='bar', color='skyblue')
    plt.title('Рекомендуемое распределение типов контента (%)')
    plt.ylabel('Процент от общего числа постов')
    plt.savefig('graphs/strategy_content_types.png')
    plt.close()

def main():
    os.makedirs('graphs', exist_ok=True)
    os.makedirs('competitors_data', exist_ok=True)
    
    print("Загрузка данных...")
    data = load_data()
    
    if 'subscribers' in data and 'interests' in data['subscribers'].columns:
        interests = analyze_interests(data['subscribers'])
        top_interests = interests.most_common(10)
        print("\nТОП-10 интересов аудитории:")
        for interest, count in top_interests:
            print(f"{interest}: {count}")
    else:
        print("\nНет данных об интересах подписчиков")
    
    print("\nГенерация стратегии...")
    strategy = generate_content_strategy(data)
    
    print("\nСТРАТЕГИЯ РАЗВИТИЯ СООБЩЕСТВА:")
    print("\n1. Рекомендации по контенту:")
    for rec in strategy['content_types'] or ["Недостаточно данных для рекомендаций"]:
        print(f"- {rec}")
    
    print("\n2. Лучшее время для публикаций:")
    print(f"- Часы: {', '.join(map(str, strategy['posting_schedule'].get('best_hours', [])))}")
    print(f"- Дни: {', '.join(strategy['posting_schedule'].get('best_days', []))}")
    
    print("\n3. Коллаборации:")
    for collab in strategy['collaborations'] or ["Недостаточно данных для рекомендаций"]:
        print(f"- {collab}")
    
    print("\n4. Целевые показатели (KPI):")
    for k, v in strategy['kpi'].items():
        print(f"- {k}: {v}")
    
    visualize_strategy(strategy)
    print("\nГрафики стратегии сохранены в папке graphs")

if __name__ == "__main__":
    main()
