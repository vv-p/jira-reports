### Описание

**Для запуска используйте Python 3 (я тестировал работу с Python3.6).**

* **daily_report.py** - генерит отчёт по работе за предыдущий рабочий день (в понедельник сгенерит для пятницы) для команды
* **weekly_report.py** - отчёт по работе за неделю
* **testing_queue.py** - список задач для команды тестирования на день

### Подготовка к работе

Для работы нужно сделать конфиг с логинами-паролями, например, такой:

> cat settings.yaml

```yaml
jira:
    url: https://jira.localhost.localdomain/
    user: stuff@mlocalhost.localdomain
    pass: 1q2w3e4r
    project: PRJ

smtp:
    host: smtp.localhost.localdomain
    port: 465
    user: ecstatic_golick@localhost.localdomain
    pass: r4e3w2q1

team:
  - mail: mad_bhaskara@localhost.localdomain
    role: manual
  - mail: compassionate_pare@localhost.localdomain
    role: manual
  - mail: peaceful_shirley@localhost.localdomain
    role: auto
  - mail: trusting_minsky@localhost.localdomain
    role: auto
  - mail: determined_stallman@localhost.localdomain
    role: auto

email:
    from: jira_reports@localhost.localdomain
    to: serene_newton@localhost.localdomain
    daily_subject: 'Daily report {}'
    queue_subject: "Очередь тестирования {}"
    ages_subject: "Ages report"
    weekly_subject: "Отчёт {} - {}"
```

Этот конфиг автоматично загрузится в процессе работы любого скрипта. Очередь задач, отчёты по работе за день и за неделю
строятся для сотрудников с **role=manual**. 


### Разное

* Все скрипты поддерживают расширенное логирование, оно включается опцией -v:

```
python3.6 daily_report -v
...
DEBUG:requests.packages.urllib3.connectionpool:https://jira.localhost.localdomain:443 "GET /rest/api/2/issue/PRJ-26013/worklog HTTP/1.1" 200 None
DEBUG:__main__:Skip worklog in PRJ-26013, it has started date = 20-04-2017
DEBUG:__main__:Skip worklog in PRJ-26013, it has started date = 24-04-2017
DEBUG:__main__:Skip worklog in PRJ-26013, it has started date = 25-04-2017
...
```

* Если очень хочется запустить код в Python2.7, нужно поправить руками одно место - в шаблоне
**templates/testing_queue.html** изменить

```jinja2
    {% for key, task in tasks.items() %}
```

на

```jinja2
    {% for key, task in tasks.iteritems() %}
```

