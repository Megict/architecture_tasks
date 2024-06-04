## Лабораторная работа 5

### Результат работы wrk

Запуск с кэшем

    Running 30s test @ http://localhost:8000
      12 threads and 400 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency     1.17s   529.27ms   1.99s    61.38%
        Req/Sec    26.33     22.85   121.00     67.18%
      2872 requests in 30.09s, 2.03MB read
      Socket errors: connect 0, read 0, write 0, timeout 2683
    Requests/sec:     95.43
    Transfer/sec:     69.21KB

Запуск без кеша

    Running 30s test @ http://localhost:8000
      12 threads and 400 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency     1.04s   520.47ms   1.97s    58.46%
        Req/Sec    17.81     15.70    80.00     66.98%
      1170 requests in 30.09s, 850.80KB read
      Socket errors: connect 0, read 0, write 0, timeout 1105
    Requests/sec:     38.88
    Transfer/sec:     28.27KB
