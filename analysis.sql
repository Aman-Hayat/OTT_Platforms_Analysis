-- 1) Total titles by platform
SELECT platform, COUNT(*) AS total_titles
FROM dbo.ott_content
GROUP BY platform
ORDER BY total_titles DESC;

-- 2) Movies vs TV Shows by platform
SELECT platform, type, COUNT(*) AS total_titles
FROM dbo.ott_content
GROUP BY platform, type
ORDER BY platform, type;

-- 3) Titles released each year
SELECT release_year, COUNT(*) AS total_titles
FROM dbo.ott_content
GROUP BY release_year
ORDER BY release_year DESC;

-- 4) Distinct countries (excluding NULL/blank)
SELECT DISTINCT LTRIM(RTRIM(country)) AS country
FROM dbo.ott_content
WHERE NULLIF(LTRIM(RTRIM(country)), '') IS NOT NULL
ORDER BY country;

-- 5) Top 10 genres per platform (SQL Server way)
WITH exploded AS (
    SELECT
        platform,
        LTRIM(RTRIM(value)) AS genre
    FROM dbo.ott_content
    CROSS APPLY STRING_SPLIT(listed_in, ',')
    WHERE NULLIF(LTRIM(RTRIM(listed_in)), '') IS NOT NULL
),
counts AS (
    SELECT
        platform,
        genre,
        COUNT(*) AS genre_count
    FROM exploded
    WHERE NULLIF(genre, '') IS NOT NULL
    GROUP BY platform, genre
),
ranked AS (
    SELECT
        platform,
        genre,
        genre_count,
        ROW_NUMBER() OVER (
            PARTITION BY platform
            ORDER BY genre_count DESC, genre
        ) AS rn
    FROM counts
)
SELECT platform, genre, genre_count
FROM ranked
WHERE rn <= 10
ORDER BY platform, genre_count DESC, genre;

-- 6) Duplicates check for data quality
SELECT
    title,
    platform,
    COUNT(*) AS occurrences
FROM ott_content
GROUP BY
    title,
    platform
HAVING COUNT(*) > 1
ORDER BY
    title,
    platform;

