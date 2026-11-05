# Sorting: inferred complexity vs textbook

| algorithm | distribution | metric | measured | exponent | textbook | match |
|---|---|---|---|---|---|---|
| bubble | random | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| bubble | sorted | comparisons | O(n) | 1.01 | O(n) | yes |
| bubble | reversed | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| bubble | nearly_sorted | comparisons | O(n^2) | 2.14 |  | - |
| bubble | few_unique | comparisons | O(n^2) | 2.01 |  | - |
| insertion | random | comparisons | O(n^2) | 2.0 | O(n^2) | yes |
| insertion | sorted | comparisons | O(n) | 1.01 | O(n) | yes |
| insertion | reversed | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| insertion | nearly_sorted | comparisons | O(n^2) | 1.94 |  | - |
| insertion | few_unique | comparisons | O(n^2) | 1.99 |  | - |
| selection | random | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| selection | sorted | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| selection | reversed | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| selection | nearly_sorted | comparisons | O(n^2) | 2.01 |  | - |
| selection | few_unique | comparisons | O(n^2) | 2.01 |  | - |
| quick_naive | random | comparisons | O(n log n) | 1.26 | O(n log n) | yes |
| quick_naive | sorted | comparisons | O(n^2) | 2.01 | O(n^2) | yes |
| quick_naive | reversed | comparisons | O(n^2) | 1.99 | O(n^2) | yes |
| quick_naive | nearly_sorted | comparisons | O(n log n) | 1.28 |  | - |
| quick_naive | few_unique | comparisons | O(n^2) | 1.81 |  | - |
| shell | random | comparisons | O(n log n) | 1.22 |  | - |
| shell | sorted | comparisons | O(n log n) | 1.2 |  | - |
| shell | reversed | comparisons | O(n log n) | 1.18 |  | - |
| shell | nearly_sorted | comparisons | O(n log n) | 1.26 |  | - |
| shell | few_unique | comparisons | O(n log n) | 1.16 |  | - |
| merge | random | comparisons | O(n log n) | 1.18 | O(n log n) | yes |
| merge | sorted | comparisons | O(n log n) | 1.16 | O(n log n) | yes |
| merge | reversed | comparisons | O(n log n) | 1.15 | O(n log n) | yes |
| merge | nearly_sorted | comparisons | O(n log n) | 1.22 |  | - |
| merge | few_unique | comparisons | O(n log n) | 1.18 |  | - |
| quick_median3 | random | comparisons | O(n log n) | 1.12 | O(n log n) | yes |
| quick_median3 | sorted | comparisons | O(n log n) | 1.12 | O(n log n) | yes |
| quick_median3 | reversed | comparisons | O(n log n) | 1.12 | O(n log n) | yes |
| quick_median3 | nearly_sorted | comparisons | O(n log n) | 1.12 |  | - |
| quick_median3 | few_unique | comparisons | O(n log n) | 1.11 |  | - |
| heap | random | comparisons | O(n log n) | 1.19 | O(n log n) | yes |
| heap | sorted | comparisons | O(n log n) | 1.19 | O(n log n) | yes |
| heap | reversed | comparisons | O(n log n) | 1.2 | O(n log n) | yes |
| heap | nearly_sorted | comparisons | O(n log n) | 1.19 |  | - |
| heap | few_unique | comparisons | O(n log n) | 1.18 |  | - |
| timsort | random | comparisons | O(n log n) | 1.18 | O(n log n) | yes |
| timsort | sorted | comparisons | O(n) | 1.0 | O(n) | yes |
| timsort | reversed | comparisons | O(n) | 1.0 | O(n) | yes |
| timsort | nearly_sorted | comparisons | O(n) | 1.08 |  | - |
| timsort | few_unique | comparisons | O(n) | 1.07 |  | - |
| counting | random | writes | O(n) | 1.0 | O(n) | yes |
| counting | sorted | writes | O(n) | 1.0 | O(n) | yes |
| counting | reversed | writes | O(n) | 1.0 | O(n) | yes |
| counting | nearly_sorted | writes | O(n) | 1.0 | O(n) | yes |
| counting | few_unique | writes | O(n) | 1.0 | O(n) | yes |
| radix | random | writes | O(n log n) | 1.12 | O(n log n) | yes |
| radix | sorted | writes | O(n log n) | 1.12 | O(n log n) | yes |
| radix | reversed | writes | O(n log n) | 1.12 | O(n log n) | yes |
| radix | nearly_sorted | writes | O(n log n) | 1.12 | O(n log n) | yes |
| radix | few_unique | writes | O(n) | 1.0 | O(n) | yes |
