# RetailPulse Data Profiling & Quality Assessment Report

## 1. Executive Summary
- **Original Source Dataset:** `data/raw/Sample-Superstore.csv` (3,295 records, 21 columns)
- **Representative Sample:** `data/raw/superstore_sample_1000.csv` (1,000 records)
- **Encoding:** UTF-8
- **Duplicate Records (Full Row):** 0
- **Row ID Duplicates:** 0

## 2. Column-Level Profiling
| Column Name | Data Type | Missing Count | Missing % | Unique Values | Sample Values |
|-------------|-----------|---------------|-----------|---------------|---------------|
| **Row ID** | `int64` | 0 | 0.0% | 3295 | `1, 2, 3` |
| **Order ID** | `str` | 0 | 0.0% | 1639 | `CA-2017-152156, CA-2017-152156, CA-2017-138688` |
| **Order Date** | `str` | 0 | 0.0% | 861 | `11/8/2017, 11/8/2017, 6/12/2017` |
| **Ship Date** | `str` | 0 | 0.0% | 914 | `11/11/2017, 11/11/2017, 6/16/2017` |
| **Ship Mode** | `str` | 0 | 0.0% | 4 | `Second Class, Second Class, Second Class` |
| **Customer ID** | `str` | 0 | 0.0% | 701 | `CG-12520, CG-12520, DV-13045` |
| **Customer Name** | `str` | 1 | 0.03% | 700 | `Claire Gute, Claire Gute, Darrin Van Huff` |
| **Segment** | `str` | 1 | 0.03% | 3 | `Consumer, Consumer, Corporate` |
| **Country** | `str` | 1 | 0.03% | 1 | `United States, United States, United States` |
| **City** | `str` | 1 | 0.03% | 358 | `Henderson, Henderson, Los Angeles` |
| **State** | `str` | 1 | 0.03% | 46 | `Kentucky, Kentucky, California` |
| **Postal Code** | `float64` | 2 | 0.061% | 439 | `42420.0, 42420.0, 90036.0` |
| **Region** | `str` | 1 | 0.03% | 4 | `South, South, West` |
| **Product ID** | `str` | 1 | 0.03% | 1520 | `FUR-BO-10001798, FUR-CH-10000454, OFF-LA-10000240` |
| **Category** | `str` | 1 | 0.03% | 3 | `Furniture, Furniture, Office Supplies` |
| **Sub-Category** | `str` | 1 | 0.03% | 17 | `Bookcases, Chairs, Labels` |
| **Product Name** | `str` | 1 | 0.03% | 1507 | `Bush Somerset Collection Bookcase, Hon Deluxe Fabric Upholstered Stacking Chairs, Rounded Back, Self-Adhesive Address Labels for Typewriters by Universal` |
| **Sales** | `float64` | 1 | 0.03% | 2585 | `261.96, 731.94, 14.62` |
| **Quantity** | `float64` | 1 | 0.03% | 14 | `2.0, 3.0, 2.0` |
| **Discount** | `float64` | 1 | 0.03% | 12 | `0.0, 0.0, 0.0` |
| **Profit** | `float64` | 1 | 0.03% | 2868 | `41.9136, 219.582, 6.8714` |

## 3. Date & Numeric Quality Checks
- **Order Date Range:** 2015-01-04 00:00:00 to 2018-12-30 00:00:00 (Invalid dates: 0)
- **Ship Date Range:** 2015-01-08 00:00:00 to 2019-01-05 00:00:00 (Invalid dates: 0)
- **Sales Metrics:** Min = $0.88, Max = $22,638.48, Mean = $235.98
- **Profit Metrics:** Min = $-3,839.99, Max = $3,919.99, Negative Profits (Losses) = 593
- **Quantity Metrics:** Min = 1.0, Max = 14.0

## 4. Identified Real Quality Issues
1. **Missing Postal Codes:** Burlington, Vermont records (e.g. Row ID 2235) have null postal codes.
2. **Corrupted / Empty Record:** Row ID 3295 is missing sales, profit, quantity, customer, and category data.
3. **No Double-Counting:** The dataset provides pre-computed line-item `Sales`. Transformations must NOT multiply `Sales` by `Quantity`.
