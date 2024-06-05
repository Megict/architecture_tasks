## Лабораторная работа 5

### Результат работы wrk
### Со сложными запросами

Запуск с кэшем

    Running 30s test @ http://localhost:8000
      1 threads and 10 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency    91.71ms    8.55ms 144.63ms   81.67%
        Req/Sec   109.30     11.58   131.00     79.00%
      Latency Distribution
         50%   88.38ms
         75%   95.91ms
         90%  103.96ms
         99%  120.03ms
      3267 requests in 30.02s, 2.18MB read
    Requests/sec:    108.83
    Transfer/sec:     74.33KB

Запуск без кеша
    
    Running 30s test @ http://localhost:8000
      1 threads and 10 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency   250.23ms   59.09ms 493.61ms   67.31%
        Req/Sec    39.77     14.66    90.00     70.33%
      Latency Distribution
         50%  247.98ms
         75%  283.95ms
         90%  323.91ms
         99%  383.93ms
      1193 requests in 30.01s, 838.43KB read
    Requests/sec:     39.75
    Transfer/sec:     27.93KB

-------------------------------------------------------------------------
### Только с простыми запросами чтения

Запуск с кешем

    Running 30s test @ http://localhost:8000
      1 threads and 10 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency    84.30ms    7.38ms 135.99ms   78.18%
        Req/Sec   118.80     10.15   131.00     69.33%
      Latency Distribution
         50%   83.95ms
         75%   87.90ms
         90%   91.88ms
         99%  115.60ms
      3552 requests in 30.01s, 635.51KB read
    Requests/sec:    118.35
    Transfer/sec:     21.17KB


Запуск без кеша

    Running 30s test @ http://localhost:8000
      1 threads and 10 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency    85.74ms    6.92ms 170.62ms   91.04%
        Req/Sec   116.91      9.95   140.00     82.00%
      Latency Distribution
         50%   83.99ms
         75%   87.96ms
         90%   91.94ms
         99%  111.97ms
      3493 requests in 30.01s, 624.97KB read
    Requests/sec:    116.38
    Transfer/sec:     20.82KB


