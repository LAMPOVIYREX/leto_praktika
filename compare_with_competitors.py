import vk_api
import pandas as pd
import os
import matplotlib.pyplot as plt
import time

os.makedirs('graphs', exist_ok=True)

token = 'ТОКЕН'
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

competitors = ['public_2010pervolit', 'lazercut', 'secreto_workshop', 'club226755060', 'krona_lazer52']
results = []

for group in competitors:
    try:
        info = vk.groups.getById(group_id=group)
        members = vk.groups.getMembers(group_id=group, count=1)['count']
        results.append({
            'group': group,
            'name': info[0]['name'],
            'members_count': members
        })
    except Exception as e:
        print(f"Ошибка при обработке группы {group}: {e}")
    time.sleep(1)

df_competitors = pd.DataFrame(results)
df_competitors.to_csv('competitors.csv', index=False)

df_competitors.set_index('group')['members_count'].plot(kind='bar', title='Сравнение количества подписчиков')
plt.xlabel('Группа')
plt.ylabel('Число подписчиков')
plt.savefig('graphs/competitors_comparison.png')
plt.show()
