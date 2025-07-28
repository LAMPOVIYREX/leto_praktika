import vk_api
import pandas as pd
import time
import json
import os
from datetime import datetime

TOKEN = 'ТОКЕН'
VERSION = '5.131'
os.makedirs('competitors_data', exist_ok=True)

GROUPS = {
    'main': {'name': 'laser33', 'id': -165542199},
    'competitors': [
        {'name': 'lazercut', 'id': -24832322},
        {'name': 'secreto_workshop', 'id': -216182561},
        {'name': 'krona_lazer52', 'id': -193056484},
        {'name': 'pervolazer', 'id': -103874968},
        {'name': 'lazer_mix', 'id': -226755060}
    ]
}

class VKDataCollector:
    def __init__(self, token, version):
        self.vk_session = vk_api.VkApi(token=token)
        self.vk = self.vk_session.get_api()
        self.version = version

    def get_group_members(self, group_id, fields='sex,bdate,city,country,interests,education,career,last_seen'):
        try:
            count = self.vk.groups.getMembers(group_id=group_id, count=0)['count']
            members = []
            for offset in range(0, count, 1000):
                response = self.vk.groups.getMembers(
                    group_id=group_id,
                    count=1000,
                    offset=offset,
                    fields=fields,
                    v=self.version
                )
                members.extend(response['items'])
                time.sleep(0.5)
                print(f"Собрано {len(members)}/{count} подписчиков")
            return members
        except Exception as e:
            print(f"Ошибка при получении подписчиков: {e}")
            return []

    def process_user_data(self, user):
        data = {
            'id': user.get('id'),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'sex': user.get('sex'),
            'city': user.get('city', {}).get('title', '') if 'city' in user else '',
            'country': user.get('country', {}).get('title', '') if 'country' in user else ''
        }
        if 'bdate' in user:
            bdate = user['bdate'].split('.')
            if len(bdate) == 3:
                birth_year = int(bdate[2])
                data['age'] = datetime.now().year - birth_year
        if 'education' in user:
            data.update({
                'university': user['education'].get('university_name', ''),
                'faculty': user['education'].get('faculty_name', '')
            })
        if 'career' in user and user['career']:
            data['position'] = user['career'][0].get('position', '')
        if 'last_seen' in user:
            data['last_seen'] = datetime.fromtimestamp(user['last_seen']['time']).strftime('%Y-%m-%d %H:%M')
        data['interests'] = user.get('interests', '')
        return data

    def save_group_data(self, group_name, members_data):
        df = pd.DataFrame(members_data)
        if group_name == 'main':
            filename = 'subscribers.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"Данные сохранены в {filename}")
        else:
            filename = f"competitors_data/{group_name}_subscribers.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            meta = {
                'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'total_members': len(df),
                'avg_age': df['age'].mean(),
                'top_cities': df['city'].value_counts().head(3).to_dict()
            }
            with open(f"competitors_data/{group_name}_meta.json", 'w') as f:
                json.dump(meta, f)
            print(f"Данные по {group_name} сохранены в {filename}")

    def collect_all_data(self):
        print(f"\nСбор данных для основной группы {GROUPS['main']['name']}")
        main_members = self.get_group_members(abs(GROUPS['main']['id']))
        main_data = [self.process_user_data(u) for u in main_members]
        self.save_group_data('main', main_data)
        for group in GROUPS['competitors']:
            print(f"\nСбор данных для конкурента {group['name']}")
            members = self.get_group_members(abs(group['id']))
            processed = [self.process_user_data(u) for u in members]
            self.save_group_data(group['name'], processed)
            time.sleep(5)

if __name__ == "__main__":
    collector = VKDataCollector(TOKEN, VERSION)
    collector.collect_all_data()
