# Resumen de experimentos

Fuente: `results/experiments_bench.csv`

| instance | solver | n_selected | duration_utilization | solver_score | mean_relevance | mean_coherence | objective_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| example_instance.json | baseline | 5 | 1 | 5.788 | 0.780 | 0.500 | 3.425 |
| example_instance.json | llm_dynamic | 5 | 1 | 4.600 | 0.780 | 0.700 | 3.625 |
| example_instance.json | llm_static | 5 | 1 | 4.400 | 0.780 | 0.500 | 3.425 |
| example_instance_overlimit.json | baseline | 3 | 0.900 | 3.400 | 0.767 | 0.500 | 1.975 |
| example_instance_overlimit.json | llm_dynamic | 3 | 0.900 | 2.950 | 0.833 | 0.900 | 2.325 |
| example_instance_overlimit.json | llm_static | 3 | 0.933 | 2.850 | 0.867 | 0.500 | 2.200 |
| bench_static_vs_dynamic.json | baseline | 2 | 1 | 2.225 | 0.550 | 0.800 | 1.025 |
| bench_static_vs_dynamic.json | llm_dynamic | 2 | 1 | 2 | 0.900 | 0.800 | 1.550 |
| bench_static_vs_dynamic.json | llm_static | 2 | 1 | 2.050 | 0.900 | 0.800 | 1.550 |
| bench_irrelevant_middle.json | baseline | 1 | 0.744 | 1 | 0.800 | 0.000 | 0.600 |
| bench_irrelevant_middle.json | llm_dynamic | 1 | 0.930 | 0.900 | 0.900 | 0.000 | 0.675 |
| bench_irrelevant_middle.json | llm_static | 1 | 0.744 | 1.025 | 0.800 | 0.000 | 0.600 |
| bench_disordered.json | baseline | 4 | 1 | 4.588 | 0.625 | 0.333 | 2.125 |
| bench_disordered.json | llm_dynamic | 4 | 1 | 4.025 | 0.850 | 0.833 | 3.175 |
| bench_disordered.json | llm_static | 4 | 1 | 3.650 | 0.850 | 0.600 | 3.000 |
