import vk_api
import pandas as pd
from datetime import datetime
import time
import matplotlib.pyplot as plt
import os
import json
from tqdm import tqdm

os.makedirs('competitors_data', exist_ok=True)
os.makedirs('graphs', exist_ok=True)

TOKEN = 'ТОКЕН'
VERSION = '5.131'
COMPETITORS = [
    {'name': 'Лазерная резка Невский', 'id': -24832322, 'screen_name': 'lazercut'},
    {'name': 'Secreto Пермь', 'id': -216182561, 'screen_name': 'secreto_workshop'},
    {'name': 'Lazer Mix', 'id': -226755060, 'screen_name': 'club226755060'},
    {'name': 'Крона', 'id': -193056484, 'screen_name': 'krona_lazer52'},
    {'name': 'Перволазер', 'id': -103874968, 'screen_name': 'public_2010pervolit'}
]

def get_competitor_posts(group_id, days_back=90):
    try:
        end_date = datetime.now().timestamp()
        start_date = end_date - days_back * 86400
        
        all_posts = []
        offset = 0
        retries = 3
        
        for attempt in range(retries):
            try:
                while True:
                    posts = vk_session.method('wall.get', {
                        'owner_id': group_id,
                        'count': 100,
                        'offset': offset,
                        'v': VERSION
                    })
                    
                    if not posts.get('items'):
                        break
                        
                    for post in posts['items']:
                        post_date = post['date']
                        if post_date < start_date:
                            return all_posts
                            
                        all_posts.append({
                            'id': post['id'],
                            'date': datetime.fromtimestamp(post['date']).strftime('%Y-%m-%d %H:%M'),
                            'text': post.get('text', ''),
                            'likes': post.get('likes', {}).get('count', 0),
                            'reposts': post.get('reposts', {}).get('count', 0),
                            'comments': post.get('comments', {}).get('count', 0),
                            'views': post.get('views', {}).get('count', 0),
                            'attachments': len(post.get('attachments', []))
                        })
                    
                    offset += 100
                    time.sleep(0.5)
                
                return all_posts
                
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Ошибка при получении постов (попытка {attempt + 1}): {str(e)}")
                    return []
                time.sleep(2)
                continue
                
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        return []

def analyze_content_types(posts):
    content_types = {
        'case_study': 0,
        'promo': 0,
        'educational': 0,
        'news': 0,
        'entertainment': 0
    }
    
    for post in posts:
        text = post['text'].lower()
        if any(w in text for w in ['кейс', 'пример', 'реализац']):
            content_types['case_study'] += 1
        elif any(w in text for w in ['акция', 'скидк', 'предложен']):
            content_types['promo'] += 1
        elif any(w in text for w in ['обучен', 'курс', 'технолог']):
            content_types['educational'] += 1
        elif any(w in text for w in ['новост', 'событ', 'мероприят']):
            content_types['news'] += 1
        else:
            content_types['entertainment'] += 1
    
    return content_types

def save_competitor_data(competitor, posts):
    try:
        if not posts:
            print(f"Нет постов для сохранения: {competitor['name']}")
            return False
            
        df = pd.DataFrame(posts)
        filename_csv = f"competitors_data/{competitor['screen_name']}_content.csv"
        df.to_csv(filename_csv, index=False, encoding='utf-8-sig')
        
        stats = {
            'total_posts': len(posts),
            'avg_likes': round(df['likes'].mean(), 1),
            'avg_reposts': round(df['reposts'].mean(), 1),
            'content_types': analyze_content_types(posts)
        }
        
        filename_json = f"competitors_data/{competitor['screen_name']}_stats.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"Сохранено {len(posts)} постов для {competitor['name']} ({competitor['screen_name']})")
        return True
        
    except Exception as e:
        print(f"Ошибка при сохранении данных для {competitor['name']}: {str(e)}")
        return False

def get_group_subscribers(group_id):
    try:
        group_info = vk_session.method('groups.getById', {
            'group_id': abs(group_id),
            'fields': 'members_count',
            'v': VERSION
        })
        return group_info[0]['members_count']
    except:
        return 0

def visualize_comparison(main_group, competitors):
    plt.figure(figsize=(12, 6))
    
    for comp in competitors:
        if comp['subscribers'] > 0:
            er = (comp['avg_likes'] + comp['avg_reposts']) / comp['subscribers'] * 100
            plt.bar(comp['name'], er, label=f"{comp['subscribers']} подписчиков")
    
    if main_group['subscribers'] > 0:
        main_er = (main_group['avg_likes'] + main_group['avg_reposts']) / main_group['subscribers'] * 100
        plt.bar('Laser33 (основная)', main_er, color='red')
    
    plt.title('Сравнение вовлеченности (ER)')
    plt.ylabel('Engagement Rate (%)')
    plt.legend()
    plt.savefig('graphs/engagement_comparison.png')
    plt.close()

if __name__ == "__main__":
    try:
        vk_session = vk_api.VkApi(token=TOKEN)
        vk = vk_session.get_api()
        
        main_group_stats = {
            'subscribers': 1200,
            'avg_likes': 12.3,
            'avg_reposts': 1.8
        }
        
        competitors_stats = []
        successful_groups = 0
        
        print("\nНачало анализа конкурентов...")
        for competitor in tqdm(COMPETITORS, desc="Обработка сообществ"):
            try:
                print(f"\nАнализируем {competitor['name']} ({competitor['screen_name']})...")
                posts = get_competitor_posts(competitor['id'])
                
                if not posts:
                    print(f"Не удалось получить посты для {competitor['name']}")
                    continue
                
                subscribers = get_group_subscribers(competitor['id'])
                if subscribers == 0:
                    print(f"Не удалось получить количество подписчиков для {competitor['name']}")
                    continue
                
                avg_likes = sum(p['likes'] for p in posts) / len(posts)
                avg_reposts = sum(p['reposts'] for p in posts) / len(posts)
                
                if save_competitor_data(competitor, posts):
                    competitors_stats.append({
                        'name': competitor['name'],
                        'subscribers': subscribers,
                        'avg_likes': avg_likes,
                        'avg_reposts': avg_reposts,
                        'content_types': analyze_content_types(posts)
                    })
                    successful_groups += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Ошибка при обработке {competitor['name']}: {str(e)}")
                continue
        
        print(f"\nУспешно обработано {successful_groups} из {len(COMPETITORS)} сообществ")
        
        if successful_groups > 0:
            visualize_comparison(main_group_stats, competitors_stats)
            print("\nГрафик сравнения сохранён в graphs/engagement_comparison.png")
        else:
            print("\nНедостаточно данных для визуализации")
            
    except Exception as e:
        print(f"Критическая ошибка в основном цикле: {str(e)}")
