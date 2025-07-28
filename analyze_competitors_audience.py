import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import json
import numpy as np

os.makedirs('competitors_clean', exist_ok=True)
os.makedirs('graphs/competitors', exist_ok=True)

def clean_competitor_data(raw_file):
    df = pd.read_csv(raw_file)
    df = df[df['first_name'] != 'DELETED']
    
    if 'age' in df.columns:
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        df = df[(df['age'] >= 15) & (df['age'] <= 80)]
    else:
        df['age'] = None
    
    if 'sex' in df.columns:
        gender_map = {1: 'Женский', 2: 'Мужской', 0: 'Не указан'}
        df['gender'] = df['sex'].map(gender_map)
    
    meta = {
        'cleaned_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_users': int(len(df))
    }
    
    if 'age' in df.columns and not df['age'].isnull().all():
        meta['age_mean'] = float(df['age'].mean())
    
    if 'gender' in df.columns:
        gender_dist = df['gender'].value_counts().to_dict()
        meta['gender_distribution'] = {str(k): int(v) for k, v in gender_dist.items()}
    
    return df, meta

def visualize_competitor_data(df, competitor_name):
    if 'age' in df.columns and not df['age'].isnull().all():
        plt.figure(figsize=(10, 6))
        df['age'].hist(bins=20, rwidth=0.8)
        plt.title(f'Распределение возраста: {competitor_name}')
        plt.xlabel('Возраст')
        plt.ylabel('Количество')
        plt.savefig(f'graphs/competitors/{competitor_name}_age.png')
        plt.close()
    
    if 'gender' in df.columns:
        plt.figure(figsize=(6, 6))
        df['gender'].value_counts().plot(kind='pie', autopct='%1.1f%%')
        plt.title(f'Распределение по полу: {competitor_name}')
        plt.savefig(f'graphs/competitors/{competitor_name}_gender.png')
        plt.close()
    
    if 'city' in df.columns:
        plt.figure(figsize=(10, 6))
        df['city'].value_counts().head(10).plot(kind='barh')
        plt.title(f'Топ-10 городов: {competitor_name}')
        plt.savefig(f'graphs/competitors/{competitor_name}_cities.png')
        plt.close()

def process_all_competitors():
    competitors_stats = {}
    
    for file in os.listdir('competitors_data'):
        if file.endswith('_subscribers.csv'):
            competitor_name = file.replace('_subscribers.csv', '')
            print(f"\nОбработка {competitor_name}...")
            
            try:
                df, meta = clean_competitor_data(f'competitors_data/{file}')
                clean_filename = f'competitors_clean/{competitor_name}_clean.csv'
                df.to_csv(clean_filename, index=False, encoding='utf-8-sig')
                
                with open(f'competitors_clean/{competitor_name}_meta.json', 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                
                visualize_competitor_data(df, competitor_name)
                
                simple_meta = {
                    'total_users': meta['total_users'],
                    'age_mean': meta.get('age_mean', None),
                    'male_count': meta.get('gender_distribution', {}).get('Мужской', 0),
                    'female_count': meta.get('gender_distribution', {}).get('Женский', 0)
                }
                competitors_stats[competitor_name] = simple_meta
                
            except Exception as e:
                print(f"Ошибка при обработке {competitor_name}: {str(e)}")
                continue
    
    if competitors_stats:
        summary = pd.DataFrame.from_dict(competitors_stats, orient='index')
        summary.to_csv('competitors_clean/summary_stats.csv', encoding='utf-8-sig')
        print("\nСводная статистика по конкурентам:")
        print(summary)
    else:
        print("\nНет данных для сохранения сводной статистики")

if __name__ == "__main__":
    print("=== Анализ аудитории конкурентов ===")
    process_all_competitors()
    print("\nОчищенные данные сохранены в competitors_clean/")
    print("Графики сохранены в graphs/competitors/")
