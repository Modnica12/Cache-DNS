# Cache DNS server

by Щербаков Кирилл КН-203

### Example for *linux*:

run server in terminal with command: sudo python3 dns.py

then open second terminal and run *nslookup*

choose server with ip 127.0.0.1 (*server 127.0.0.1*)

after that you can send requests to dns server

Авторитетным является dns сервер, ведущий зону e1.ru

Данные, полученные от этого сервера кэшируются и отправляются пользователю

Сервер регулярно проводит "чистку" и удаляет устаревшие записи