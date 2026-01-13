-- Iterable Challenge: Phase 2
-- Data Extraction Queries

-- ==========================================
-- Query 1: Pro Users - Pricing/Settings Views
-- ==========================================
-- This query:
-- 1. Joins customers and page_views
-- 2. Filters for plan_type = 'pro'
-- 3. Finds users who viewed pricing or settings pages in last 7 days
-- 4. Returns customer info + latest qualifying page view metadata

SELECT 
    c.id,
    c.email,
    c.first_name,
    c.last_name,
    c.plan_type,
    c.candidate,
    pv.page,
    pv.device,
    pv.browser,
    pv.location,
    pv.event_time,
    ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY pv.event_time DESC) as view_rank
FROM customers c
INNER JOIN page_views pv ON c.id = pv.user_id
WHERE c.plan_type = 'pro'
    AND pv.page IN ('pricing', 'settings')
    AND pv.event_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY c.id, pv.event_time DESC;

-- ==========================================
-- Query 2: Latest View Per Pro User (Optimized)
-- ==========================================
-- Gets only the most recent qualifying page view per user using CTE

WITH ranked_views AS (
    SELECT 
        c.id,
        c.email,
        c.first_name,
        c.last_name,
        c.plan_type,
        c.candidate,
        pv.page,
        pv.device,
        pv.browser,
        pv.location,
        pv.event_time,
        ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY pv.event_time DESC) as view_rank
    FROM customers c
    INNER JOIN page_views pv ON c.id = pv.user_id
    WHERE c.plan_type = 'pro'
        AND pv.page IN ('pricing', 'settings')
        AND pv.event_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
)
SELECT 
    id,
    email,
    first_name,
    last_name,
    plan_type,
    candidate,
    page,
    device,
    browser,
    location,
    event_time
FROM ranked_views
WHERE view_rank = 1
ORDER BY event_time DESC;

-- ==========================================
-- Query 3: Summary Stats for Pro Users
-- ==========================================
-- Shows aggregate data on pro users' engagement with pricing/settings pages

SELECT 
    c.id,
    c.email,
    c.first_name,
    CONCAT(c.first_name, ' ', c.last_name) as full_name,
    COUNT(pv.id) as total_qualifying_views,
    COUNT(DISTINCT pv.page) as unique_pages_viewed,
    COUNT(DISTINCT pv.device) as devices_used,
    MIN(pv.event_time) as first_view_date,
    MAX(pv.event_time) as last_view_date,
    GROUP_CONCAT(DISTINCT pv.page ORDER BY pv.page) as pages_viewed
FROM customers c
INNER JOIN page_views pv ON c.id = pv.user_id
WHERE c.plan_type = 'pro'
    AND pv.page IN ('pricing', 'settings')
    AND pv.event_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
GROUP BY c.id, c.email, c.first_name, c.last_name
ORDER BY total_qualifying_views DESC;
