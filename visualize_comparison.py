import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from wordcloud import WordCloud
from tqdm import tqdm

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
os.makedirs('graphs', exist_ok=True)

def load_data():
    competitors = []
    
    if not os.path.exists('competitors_data'):
        print("Папка competitors_data не найдена!")
        return competitors
    
    try:
        main_df = pd.read_csv('results/posts_stats.csv')
        main_group = {
            'name': 'Laser33',
            'data': main_df
        }
    except Exception as e:
        print(f"Ошибка загрузки данных основной группы: {e}")
        main_group = None
    
    for file in tqdm(os.listdir('competitors_data'), desc="Загрузка данных конкурентов"):
        if file.endswith('_content.csv'):
            try:
                df = pd.read_csv(f'competitors_data/{file}')
                competitors.append({
                    'name': file.replace('_content.csv', '').replace('_', ' '),
                    'data': df
                })
            except Exception as e:
                print(f"Ошибка загрузки файла {file}: {e}")
    
    return main_group, competitors

def plot_content_distribution(competitors):
    if not competitors:
        print("Нет данных конкурентов для визуализации")
        return
    
    plt.figure(figsize=(14, 8))
    
    def classify_content(text):
        text = str(text).lower()
        if any(w in text for w in ['кейс', 'пример']):
            return 'case_study'
        elif any(w in text for w in ['акция', 'скидк']):
            return 'promo'
        elif any(w in text for w in ['обучен', 'технолог']):
            return 'educational'
        elif any(w in text for w in ['новост', 'событ']):
            return 'news'
        return 'other'
    
    content_data = []
    for comp in competitors:
        if 'text' not in comp['data'].columns:
            continue
            
        types = {'case_study': 0, 'promo': 0, 'educational': 0, 'news': 0, 'other': 0}
        for text in comp['data']['text']:
            content_type = classify_content(text)
            types[content_type] += 1
        
        total = sum(types.values())
        if total > 0:
            content_data.append({
                'name': comp['name'],
                'case_study': types['case_study']/total*100,
                'promo': types['promo']/total*100,
                'educational': types['educational']/total*100,
                'news': types['news']/total*100,
                'other': types['other']/total*100
            })
    
    if not content_data:
        print("Нет данных о типах контента для визуализации")
        return
    
    df = pd.DataFrame(content_data).set_index('name')
    df.plot(kind='bar', stacked=True, figsize=(14, 8))
    plt.title('Распределение типов контента (%)')
    plt.xlabel('Сообщество')
    plt.ylabel('Процент от общего числа постов')
    plt.legend(title='Тип контента')
    plt.tight_layout()
    plt.savefig('graphs/content_types_comparison.png')
    plt.close()

def plot_engagement_trends(main_group, competitors):
    if not competitors or main_group is None:
        print("Недостаточно данных для сравнения вовлеченности")
        return
    
    plt.figure(figsize=(14, 8))
    
    try:
        main_df = main_group['data']
        main_df['date'] = pd.to_datetime(main_df['date'])
        main_df['engagement'] = main_df['likes'] + main_df['reposts']*2
        main_weekly = main_df.set_index('date').resample('W')['engagement'].mean()
        plt.plot(main_weekly.index, main_weekly.values, 
                label='Laser33 (основная)', linewidth=3, color='red')
    except Exception as e:
        print(f"Ошибка обработки данных основной группы: {e}")
    
    for comp in competitors:
        try:
            comp_df = comp['data']
            comp_df['date'] = pd.to_datetime(comp_df['date'])
            comp_df['engagement'] = comp_df['likes'] + comp_df['reposts']*2
            weekly = comp_df.set_index('date').resample('W')['engagement'].mean()
            plt.plot(weekly.index, weekly.values, 
                    label=comp['name'], linestyle='--')
        except Exception as e:
            print(f"Ошибка обработки данных {comp['name']}: {e}")
    
    plt.title('Динамика вовлеченности по неделям')
    plt.ylabel('Средняя вовлеченность (лайки + 2*репосты)')
    plt.legend()
    plt.grid()
    plt.savefig('graphs/engagement_trends.png')
    plt.close()

if __name__ == "__main__":
    print("=== Визуализация сравнения с конкурентами ===")
    main_group, competitors = load_data()
    plot_content_distribution(competitors)
    plot_engagement_trends(main_group, competitors)
    print("\nГрафики сохранены в папке graphs:")
    print("- content_types_comparison.png")
    print("- engagement_trends.png")
